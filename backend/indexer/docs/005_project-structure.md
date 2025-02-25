wesmol/
│
├── backend/
│   ├── api/                          # TODO
│   ├── indexer/                      # Main package
│   │   ├── indexer/                  # Core indexer code
│   │   │   ├── __init__.py           # Package exports
│   │   │   ├── env.py                # Environment configuration
│   │   │   │
│   │   │   ├── contracts/            # Contract handling
│   │   │   │   ├── __init__.py
│   │   │   │   ├── manager.py        # Contract instance management
│   │   │   │   └── registry.py       # Contract metadata registry
│   │   │   │
│   │   │   ├── database/             # Database operations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models/           # SQLAlchemy models
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── base.py       # Base model class
│   │   │   │   │   └── status.py     # Processing status models
│   │   │   │   │
│   │   │   │   ├── operations/       # Database operations
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── manager.py    # DB operations
│   │   │   │   │   └── session.py    # Session management
│   │   │   │   │
│   │   │   │   └── schema/           # TODO
│   │   │   │
│   │   │   ├── decoders/             # Blockchain data decoders
│   │   │   │   ├── __init__.py
│   │   │   │   ├── block.py          # Block decoder
│   │   │   │   ├── log.py            # Event log decoder 
│   │   │   │   └── transaction.py    # Transaction decoder
│   │   │   │
│   │   │   ├── model/                # Data models
│   │   │   │   ├── __init__.py
│   │   │   │   ├── block.py          # Domain block models
│   │   │   │   ├── evm.py            # EVM data models
│   │   │   │   ├── types.py          # Common type definitions
│   │   │   │   │
│   │   │   │   └── events/           # Domain event models
│   │   │   │       ├── __init__.py
│   │   │   │       ├── event.py      # Base event class
│   │   │   │       ├── mint.py       # Mint event
│   │   │   │       ├── trade.py      # Trade event
│   │   │   │       └── ...
│   │   │   │
│   │   │   ├── processing/           # Processing pipeline
│   │   │   │   ├── __init__.py
│   │   │   │   ├── factory.py        # Component factory
│   │   │   │   ├── processor.py      # Block processor
│   │   │   │   └── validator.py      # Block validator
│   │   │   │
│   │   │   ├── storage/              # Storage operations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py           # GCS base handler
│   │   │   │   └── handler.py        # Block storage handler
│   │   │   │
│   │   │   └── utils/                # Utility functions
│   │   │       ├── __init__.py
│   │   │       └── conversion/       # Data conversion utilities
│   │   │           ├── __init__.py
│   │   │           ├── base64.py
│   │   │           ├── bytes.py
│   │   │           └── ...
│   │   │
│   │   ├── config/                   # Configuration files
│   │   │   ├── contracts.json        # Contract registry config
│   │   │   └── abis/                 # ABI files for contracts
│   │   │       ├── smoljoes/
│   │   │       ├── opensea/
│   │   │       └── ...
│   │   │
│   │   ├── docs/                     # Indexer Package Documentation
│   │   │
│   │   ├── scripts/                  # Utility scripts
│   │   │   ├── __init__.py
│   │   │   ├── init_db.py            # Database initialization
│   │   │   ├── reprocess.py          # Block reprocessing
│   │   │   └── sync_gcs.py           # GCS sync utility
│   │   │
│   │   └── setup.py                  # Package setup file
│   │
│   ├── services/                     # Cloud services
│   │   ├── processor/                # Block processor service
│   │   │   ├── server/
│   │   │   │   └── main.py           # Service entry point
│   │   │   ├── Dockerfile            
│   │   │   └── requirements.txt      # TODO
│   │   │
│   │   └── indexer/                  # TODO: Event indexer service
│   │
│   └── scripts/                      # Management scripts
│       ├── README.md                 # TODO
│       ├── __init__.py               
│       ├── fix_block.py              # Block fix utility
│       ├── init_db.py                # Database initialization script
│       └── reprocess.py              # Reprocessing utility
│
├── frontend/                         # TODO:
│
├── infrastructure/                   # TODO:
│
├── venv/
├── requirements.txt
├── .env
├── .gitignore
├── README.md
└── .env.example                     # Environment template
