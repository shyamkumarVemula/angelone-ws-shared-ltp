sm_update/
│
├── core/
│   ├── __init__.py
│   ├── shared_memory.py        # 🔑 SharedMemoryManager (single source of truth)
│   ├── ws_base.py              # AngelWebSocket with reconnect/backoff
│
├── angel/
│   ├── __init__.py
│   ├── helper_angel.py         # login helpers, getHistorical, expiry/strike utils
│
├── feeds/
│   ├── __init__.py
│   ├── ws_nifty.py             # WebSocket producer (ticks → shared memory)
│
├── collector/
│   ├── __init__.py
│   ├── collect_ltp.py          # 🟢 Indicator builder (VWAP, RSI, ATR)
│
├── strategy/
│   ├── __init__.py
│   ├── trading_logic.py        # 🟢 Buy/Sell logic (consumer)
│
├── scripts/
│   ├── __init__.py
│   ├── start_all.py            # 🚀 Entry point (starts everything)
│
├── data/
│   ├── OpenAPIScripMaster.json # Cached instrument master
│   ├── ai_levels.json          # Generated AI levels (optional)
│
├── logs/
│   ├── trades.log
│   ├── system.log
│
├── config/
│   ├── __init__.py
│   ├── constants.py            # timeouts, lot size, limits
│
└── requirements.txt
