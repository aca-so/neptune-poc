import random
from os import cpu_count

import boto3
from apscheduler.schedulers.background import BackgroundScheduler
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import GraphTraversalSource
from gremlin_python.process.strategies import ReadOnlyStrategy
from pydantic import BaseModel, ConfigDict

from app.db.graph_database import GraphDatabase


class _NeptuneConnException(Exception):
    pass


class _Instance(BaseModel):
    identifier: str
    endpoint: str | None = None
    is_writer: bool
    conn: DriverRemoteConnection | None = None
    traversal: GraphTraversalSource | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class NeptuneDatabase(GraphDatabase):
    def __init__(
            self,
            cluster_id: str,
            region: str,
            pool_size: int = 1,
            port: int = 8182,
            db_name: str = 'gremlin',
            use_ssl: bool = True,
            read_from_writer: bool = True,
            recycle_connections_period: int = 5,
    ):
        """
        :param cluster_id: Neptune cluster identifier
        :param region: AWS region
        :param pool_size: Number of connections to keep open
        :param port: Neptune port
        :param db_name: Neptune database name
        :param use_ssl: Use SSL for connections
        :param read_from_writer: Read from writer instance
        :param recycle_connections_period: Period for recycling connections in minutes
        """
        self._cluster_id = cluster_id
        self._client = boto3.client('neptune', region_name=region)

        self._instances: dict[str, _Instance] = {}
        self._temp_instances: dict[str, _Instance] = {}
        self._writer_instance_identifier: str | None = None
        self._read_from_writer = read_from_writer

        self._max_workers = (cpu_count() or 1) * 5
        self._protocol = 'wss' if use_ssl else 'ws'
        self._port = port
        self._db_name = db_name
        if int(pool_size) < 1:
            raise ValueError('Pool size must be greater than 0')
        self._pool_size = int(pool_size)

        self._setup_instances()
        self._recycle_connections_period = recycle_connections_period
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self._setup_instances, 'interval', minutes=recycle_connections_period)
        self.scheduler.start()

    def _get_instances(self):
        res = self._client.describe_db_clusters(
            DBClusterIdentifier=self._cluster_id,
        )
        if not res['DBClusters']:
            raise _NeptuneConnException('No cluster found')

        cluster_members = res['DBClusters'][0]['DBClusterMembers']
        if not cluster_members:
            raise _NeptuneConnException('No cluster members found')

        for member in cluster_members:
            identifier = member['DBInstanceIdentifier']
            is_writer = member['IsClusterWriter']
            self._temp_instances[identifier] = _Instance(
                identifier=identifier,
                is_writer=is_writer,
                available=False,
            )

    def _update_instances(self):
        for instance_identifier in self._temp_instances:
            res = self._client.describe_db_instances(
                DBInstanceIdentifier=instance_identifier,
                Filters=[
                    {
                        'Name': 'db-cluster-id',
                        'Values': [self._cluster_id]
                    }
                ],
            )
            if not res['DBInstances']:
                continue
            if len(res['DBInstances']) > 1:
                raise _NeptuneConnException('More than one instance found')
            instance = res['DBInstances'][0]

            is_available = instance['DBInstanceStatus'] == 'available'
            if not is_available:
                continue
            endpoint = instance['Endpoint']['Address']
            self._temp_instances[instance_identifier].endpoint = endpoint

            if self._temp_instances[instance_identifier].is_writer:
                self._writer_instance_identifier = instance_identifier
            self._instances[instance_identifier] = self._temp_instances[instance_identifier]
        self._temp_instances = {}

    def _connect_instances(self):
        for instance in self._instances.values():
            url = f"{self._protocol}://{instance.endpoint}:{self._port}/{self._db_name}"
            conn = DriverRemoteConnection(
                url,
                'g',
                pool_size=self._pool_size,
                max_workers=self._max_workers,
                call_from_event_loop=True,
            )
            instance.conn = conn

            traversal_ = traversal().with_remote(conn)
            if not instance.is_writer:
                traversal_ = traversal_.with_strategies(ReadOnlyStrategy())
            instance.traversal = traversal_

            # Dummy query for initializing connection
            traversal_.V().limit(1).iterate()

    def _setup_instances(self):
        self._get_instances()
        self._update_instances()
        self._connect_instances()

    def get_traversal(self) -> GraphTraversalSource:
        writer = self._writer_instance_identifier
        t = self._instances[writer].traversal
        if t is None:
            raise _NeptuneConnException('No writer instance found')
        return t

    def get_read_traversal(self) -> GraphTraversalSource:
        read_identifiers = [i for i in self._instances if not self._instances[i].is_writer]
        if not read_identifiers:
            return self.get_traversal()

        if not self._read_from_writer:
            identifier = random.choice(read_identifiers)
        else:
            weights = [1, *[2 for _ in range(len(read_identifiers))]]
            identifiers = [self._writer_instance_identifier, *read_identifiers]
            identifier = random.choices(identifiers, weights, k=1)[0]

        t = self._instances[identifier].traversal
        if t is None:
            raise _NeptuneConnException(f'Traversal not initialized for instance {identifier}')
        return t

    def close(self):
        self.scheduler.shutdown()
        for instance in self._instances.values():
            if instance.conn:
                instance.conn.close()
