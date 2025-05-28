# Blockchain Transaction Tracking Bot

This bot tracks and monitors transactions across multiple blockchains and currencies, including their native tokens and popular stablecoins like USDT, USDC, and DAI. The bot is capable of notifying users about transactions, wallet updates, and more. It supports multiple blockchains like Ethereum, Solana, Avalanche, Osmosis, Cosmos, and more.

## Supported Blockchains and Currencies

The bot currently supports the following blockchains and currencies:

### EVM-based Blockchains:
- **Ethereum (ETH)**
- **Binance Smart Chain (BNB)**
- **Arbitrum (ARB)**
- **PulseChain (PLS)**
- **Polygon (POL)**
- **Avalanche (AVAX)**
- **Optimism (OP)**
- **Fantom (FTM)**
- **Custom EVM Blockchain integration**

### Non-EVM Blockchains:
- **Solana (SOL)**
- **Tron (TRX)**
- **Dogecoin (DOGE)**
- **Polkadot (DOT)**
- **NEAR Protocol (NEAR)**
- **Algorand (ALGO)**
- **TON (TON)**
- **EOS (EOS)**
- **Pi Network (PI)**
- **Cosmos (ATOM)**
- **Osmosis (OSMO)**
- **Custom Web3 Blockchain integration**

### Supported Stablecoins:
- **Tether (USDT)**
- **USD Coin (USDC)**
- **Dai (DAI)**
- **Native Coin (All Blockchain)**

### Features
- **Real-time transaction tracking**: The bot tracks all transactions in real-time for the supported blockchains and currencies.
- **Wallet Address Support**: The bot allows users to track specific multiple wallet addresses and their transaction history in a same time .
- **Currency and Token Support**: Supports both native blockchain tokens (e.g., ETH, PI, BNB) and stablecoins (e.g., DAI, USDT, USDC).
- **Transaction Notifications**: The bot sends notifications via Telegram with details about transactions, including amount, USD value, and a link to the blockchain explorer.
- **Admin Controls**: The bot includes various admin commands to manage settings like tracking configurations, adding/removing wallets, updating rates, and more.

## Installation

### Prerequisites:
Before running the bot, ensure you have the following installed:
- Python 3.7+
- `pip` (Python package installer)
- Redis (for caching)

### Setup:
1. Clone the repository:
    ```bash
    git clone https://github.com/your-repo/blockchain-tracking-bot.git
    cd blockchain-tracking-bot
    ```

2. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the root directory and fill in the following variables:
    ```bash
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_key
    TELEGRAM_TOKEN=your_telegram_token
    ```

4. Configure the blockchain settings in `blockchains.json`. This file should contain information about each supported blockchain, its RPC URLs, and token contract addresses for stablecoins like USDT, USDC, DAI.

    Example structure:
    ```json
    {
        "Ethereum": {
            "rpc": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
            "usdt_contract": "0xdac17f958d2ee523a2206206994597c13d831ec7",
            "usdc_contract": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "dai_contract": "0x6b175474e89094c44da98b954eedeac495271d0f"
        },
        "BNB": {
            "rpc": "https://bsc-dataseed.binance.org",
            "usdt_contract": "0x55d398326f99059fF775485246999027B3197955",
            "usdc_contract": "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d",
            "dai_contract": "0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3"
        },
        ...
    }
    ```

5. **Redis Setup**: If you don't have Redis installed, you can run it using Docker:
    ```bash
    docker run -p 6379:6379 redis:alpine
    ```

6. Run the bot:
    ```bash
    python main.py
    ```

### Docker Setup (Optional)
You can also run the bot using Docker for easy deployment.

1. Build the Docker image:
    ```bash
    docker-compose build
    ```

2. Start the bot and Redis services:
    ```bash
    docker-compose up
    ```

## Admin Commands

The bot supports the following admin commands to manage blockchain tracking and notifications:

- `/start`: Start the bot.
- `/pause_tracking`: Pause transaction tracking.
- `/resume_tracking`: Resume transaction tracking.
- `/start_tracking`: Start tracking transactions for a specific blockchain.
-  `/set_media` : set image ,animated video , gif etc .
- `/stop_tracking`: Stop tracking transactions for a specific blockchain.
- `/add_wallet`: Add a wallet address for a blockchain.
- `/remove_wallet`: Remove a wallet address from tracking.
- `/add_currency`: Add a currency (token) for tracking.
- `/remove_currency`: Remove a currency (token) from tracking.
- `/update_rate`: Update the exchange rate (USD value).
- `/help`: Show available commands.
- `/status`: Show the bot's current status.
- `/add_blockchain`: Add a new blockchain to the tracking list.
- `/remove_blockchain`: Remove a blockchain from the tracking list.
- `/set_message_format`: Set the notification format for transactions.
- `/clear_cache`: Clear cached data for tracking.
- `/set_group_id`: Set the group ID for notifications.
- `/set_admin_id`: Set the admin ID for controlling the bot.
- `/set_rpc_url`: Set the RPC URL for a specific blockchain.
- `/fallback_rpc`: Set a fallback RPC URL if the primary one fails.

## How It Works

1. The bot connects to each blockchain using its RPC URL.
2. It monitors new blocks and transactions, fetching them in real-time.
3. The bot checks the tracked wallet addresses and the specific currencies (like USDT, USDC, etc.).
4. When a transaction is detected, the bot sends a notification to a specified Telegram channel with details like:
    - Amount of tokens/coins
    - USD value of the transaction (based on the latest rate)
    - A link to the transaction on the blockchain explorer
    - A link of Decentralized exchanges. 

## Supported Blockchains and Currencies

The bot supports the following blockchain types:

### EVM Chains:
- **Ethereum**
- **Binance Smart Chain (BNB)**
- **Arbitrum**
- **Polygon**
- **Avalanche**
- **Optimism**
- **Fantom**
- **PulseChain**
- **Base(Coinbase)**
- **Custom EVM Blockchain integration**

### Non-EVM Chains:
- **Solana**
- **Tron**
- **Dogecoin**
- **Polkadot**
- **NEAR Protocol**
- **Algorand**
- **TON**
- **Pi Network**
- **Cosmos**
- **Osmosis**
- **Eos**
- **Custom Web3 Blockchain integration**

### Tokens:
- **USDT** (Tether)
- **USDC** (USD Coin)
- **DAI** (Dai)
- **Native coin of each Blockchain**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
