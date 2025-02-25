from indexer.indexer.env import env
from indexer.indexer.contracts.registry import ContractRegistry
from indexer.indexer.contracts.manager import ContractManager
from indexer.indexer.storage.base import GCSBaseHandler
from indexer.indexer.processing.validator import BlockValidator
from indexer.indexer.database.operations.manager import DatabaseManager
from indexer.indexer.database.operations.session import ConnectionManager

class ComponentFactory:
    _components = {}
    
    @classmethod
    def get_gcs_handler(cls):
        if 'gcs_handler' not in cls._components:
            cls._components['gcs_handler'] = GCSBaseHandler(
                bucket_name=env.get_bucket_name(),
                credentials_path=env.get_gcs_credentials()
            )
        return cls._components['gcs_handler']
    
    @classmethod
    def get_contract_registry(cls):
        if 'contract_registry' not in cls._components:
            contracts_file = env.get_path('config_dir') / 'contracts.json'
            abi_directory = env.get_path('config_dir') / 'abis'
            cls._components['contract_registry'] = ContractRegistry(contracts_file, abi_directory)
        return cls._components['contract_registry']
    
    @classmethod
    def get_contract_manager(cls):
        if 'contract_manager' not in cls._components:
            registry = cls.get_contract_registry()
            cls._components['contract_manager'] = ContractManager(registry)
        return cls._components['contract_manager']
    
    @classmethod
    def get_database_manager(cls):
        if 'db_manager' not in cls._components:
            conn_manager = ConnectionManager(env.get_db_url())
            cls._components['db_manager'] = DatabaseManager(conn_manager)
        return cls._components['db_manager']
    
    @classmethod
    def get_block_validator(cls):
        if 'block_validator' not in cls._components:
            cls._components['block_validator'] = BlockValidator()
        return cls._components['block_validator']