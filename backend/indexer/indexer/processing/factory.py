from ..env import env
from ..contracts.registry import ContractRegistry
from ..contracts.manager import ContractManager
from ..storage.base import GCSBaseHandler
from .validator import BlockValidator
from ..database.operations.manager import DatabaseManager
from ..database.operations.session import ConnectionManager
from ..storage.local import LocalBlockHandler

class ComponentFactory:
    @classmethod
    def get_gcs_handler(cls):
        handler = env.get_component('gcs_handler')
        if handler:
            return handler
        
        handler = GCSBaseHandler(
            bucket_name=env.get_bucket_name(),
            credentials_path=env.get_gcs_credentials()
        )
        env.register_component('gcs_handler', handler)
        return handler
    
    @classmethod
    def get_contract_registry(cls):
        registry = env.get_component('contract_registry')
        if registry:
            return registry
        
        contracts_file = env.get_path('config_dir') / 'contracts.json'
        abi_directory = env.get_path('config_dir') / 'abis'
        registry = ContractRegistry(contracts_file, abi_directory)
        env.register_component('contract_registry', registry)
        return registry
    
    @classmethod
    def get_contract_manager(cls):
        manager = env.get_component('contract_manager')
        if manager:
            return manager
        
        registry = cls.get_contract_registry()
        manager = ContractManager(registry)
        env.register_component('contract_manager', manager)
        return manager
    
    @classmethod
    def get_database_manager(cls):
        db_manager = env.get_component('db_manager')
        if db_manager:
            return db_manager
        
        conn_manager = ConnectionManager(env.get_db_url())
        db_manager = DatabaseManager(conn_manager)
        env.register_component('db_manager', db_manager)
        return db_manager
    
    @classmethod
    def get_block_validator(cls):
        validator = env.get_component('block_validator')
        if validator:
            return validator
        
        validator = BlockValidator()
        env.register_component('block_validator', validator)
        return validator
    