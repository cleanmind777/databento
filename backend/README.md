# Real-time Price Monitor

A real-time price monitoring system using DataBento Live API, FastAPI (SSE), and React + Vite.

## Architecture

- **Backend**: FastAPI with Server-Sent Events (SSE) streaming
- **Data Source**: DataBento Live API for real-time market data
- **Frontend**: React + Vite with native EventSource API

## Prerequisites

- Python 3.8+
- Node.js 16+
- DataBento API Key (get it from https://databento.com/)

## Setup Instructions

### Backend Setup

1. Navigate to the project root:
```bash
cd E:\code_example\Trading\DataBento
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file (copy from `.env.example`):
```bash
copy .env.example .env
```

6. Edit `.env` and add your DataBento API key:
```
DATABENTO_API_KEY=your-actual-api-key-here
```

7. Run the FastAPI server:
```bash
python backend_main.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Usage

1. Start the backend server first
2. Start the frontend development server
3. Open your browser to `http://localhost:5173`
4. Enter symbols (comma-separated, e.g., `ES.FUT,NQ.FUT`)
5. Click "Connect" to start streaming real-time prices
6. Click "Disconnect" to stop the stream

## API Endpoints

### `GET /`
Health check endpoint

### `GET /stream/prices?symbols=ES.FUT,NQ.FUT`
SSE endpoint that streams real-time price data for the specified symbols

**Query Parameters:**
- `symbols`: Comma-separated list of symbols (e.g., "ES.FUT,NQ.FUT")

**Response Format (SSE):**
```json
{
  "symbol": "ES.FUT",
  "timestamp": "1234567890000000000",
  "bid_price": 4500.25,
  "ask_price": 4500.50,
  "bid_size": 10,
  "ask_size": 15,
  "received_at": "2024-01-15T10:30:45.123456"
}
```

### `GET /symbols`
Get list of commonly traded symbols

## DataBento Configuration

The backend is configured to use:
- **Dataset**: `GLBX.MDP3` (CME Globex)
- **Schema**: `mbp-1` (Market by Price - Level 1)

You can modify these in `backend_main.py`:
```python
DATASET = "GLBX.MDP3"  # Change to your preferred dataset
SCHEMA = "mbp-1"       # Change to your preferred schema
```

Available schemas:
- `mbp-1`: Market by Price (Level 1)
- `mbp-10`: Market by Price (10 levels)
- `trades`: Trade data
- `ohlcv-1s`: OHLCV bars (1 second)

## Common Symbols

- `ES.FUT` - E-mini S&P 500
- `NQ.FUT` - E-mini NASDAQ-100
- `YM.FUT` - E-mini Dow Jones
- `RTY.FUT` - E-mini Russell 2000
- `GC.FUT` - Gold Futures
- `CL.FUT` - Crude Oil Futures

## Troubleshooting

### Connection Issues
- Ensure the backend is running on `http://localhost:8000`
- Check that your DataBento API key is valid
- Verify CORS is properly configured

### No Data Streaming
- Check if the symbols are valid for your DataBento subscription
- Verify the dataset and schema match your subscription
- Check the browser console for errors

### Performance Issues
- Limit the number of symbols being streamed
- Consider using a lower frequency schema
- Check network bandwidth

## Security Notes

- Never commit your `.env` file with API keys
- Use environment variables for sensitive configuration
- Implement rate limiting in production
- Add authentication for the SSE endpoint in production

## License

MIT
