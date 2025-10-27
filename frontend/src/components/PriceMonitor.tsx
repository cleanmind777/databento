import { useEffect, useState, useCallback } from 'react';
import './PriceMonitor.css';

interface PriceData {
  symbol: string;
  timestamp: string;
  bid_price: number | null;
  ask_price: number | null;
  bid_size: number | null;
  ask_size: number | null;
  received_at: string;
  record_type?: string;
  error?: string;
}

interface PriceMap {
  [symbol: string]: PriceData;
}

const PriceMonitor = () => {
  const [prices, setPrices] = useState<PriceMap>({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [symbols, setSymbols] = useState<string>('NQZ5,ESZ5');
  const [eventSource, setEventSource] = useState<EventSource | null>(null);

  const connectToStream = useCallback(() => {
    // Close existing connection
    if (eventSource) {
      eventSource.close();
    }

    // Clear previous state
    setError(null);
    setPrices({});

    // Create new EventSource connection
    const url = `http://localhost:8001/stream/prices?symbols=${encodeURIComponent(symbols)}`;
    const newEventSource = new EventSource(url);

    newEventSource.onopen = () => {
      console.log('✅ SSE Connection opened');
      setIsConnected(true);
      setError(null);
    };

    newEventSource.onmessage = (event) => {
      console.log('📨 Received SSE message:', event.data);
      try {
        const data = JSON.parse(event.data);
        console.log('📊 Parsed data:', data);

        // Handle status messages
        if (data.status) {
          console.log('📋 Status:', data.message);
          return;
        }

        // Handle error messages
        if (data.error) {
          console.error('❌ Error received:', data.error);
          setError(data.error);
          return;
        }

        // Handle price data
        if (data.symbol && (data.bid_price !== null || data.ask_price !== null)) {
          console.log('💰 Processing price data for symbol:', data.symbol);
          const priceData: PriceData = {
            symbol: data.symbol,
            timestamp: data.timestamp,
            bid_price: data.bid_price,
            ask_price: data.ask_price,
            bid_size: data.bid_size,
            ask_size: data.ask_size,
            received_at: data.received_at,
            record_type: data.record_type
          };

          console.log('💾 Updating prices with:', priceData);
          // Update prices map
          setPrices((prevPrices) => ({
            ...prevPrices,
            [data.symbol]: priceData,
          }));
        } else {
          console.log('⚠️ No price data in message:', data);
        }
      } catch (err) {
        console.error('❌ Error parsing SSE data:', err);
        setError('Failed to parse price data');
      }
    };

    newEventSource.onerror = (err) => {
      console.error('SSE Error:', err);
      setIsConnected(false);
      setError('Connection lost. Retrying...');

      // Auto-reconnect after 3 seconds
      setTimeout(() => {
        if (newEventSource.readyState === EventSource.CLOSED) {
          connectToStream();
        }
      }, 3000);
    };

    setEventSource(newEventSource);
  }, [symbols, eventSource]);

  const disconnectFromStream = useCallback(() => {
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
      setIsConnected(false);
      setPrices({});
    }
  }, [eventSource]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  const formatPrice = (price: number | null): string => {
    if (price === null) return 'N/A';
    return price.toFixed(2);
  };

  const formatTimestamp = (timestamp: string): string => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return timestamp;
    }
  };

  const getSpread = (bid: number | null, ask: number | null): string => {
    if (bid === null || ask === null) return 'N/A';
    return (ask - bid).toFixed(2);
  };

  return (
    <div className="price-monitor">
      <div className="header">
        <h1>Real-time Price Monitor</h1>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
        </div>
      </div>

      <div className="controls">
        <input
          type="text"
          value={symbols}
          onChange={(e) => setSymbols(e.target.value)}
          placeholder="Enter symbols (comma-separated)"
          className="symbol-input"
          disabled={isConnected}
        />
        <button
          onClick={isConnected ? disconnectFromStream : connectToStream}
          className={`control-button ${isConnected ? 'disconnect' : 'connect'}`}
        >
          {isConnected ? 'Disconnect' : 'Connect'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      <div className="price-grid">
        {Object.keys(prices).length === 0 && isConnected && (
          <div className="loading">Waiting for price data...</div>
        )}

        {Object.entries(prices).map(([symbol, data]) => (
          <div key={symbol} className="price-card">
            <div className="symbol-header">{symbol}</div>

            <div className="price-row">
              <div className="price-column bid">
                <div className="label">Bid</div>
                <div className="price">{formatPrice(data.bid_price)}</div>
                <div className="size">{data.bid_size || 'N/A'}</div>
              </div>

              <div className="price-column ask">
                <div className="label">Ask</div>
                <div className="price">{formatPrice(data.ask_price)}</div>
                <div className="size">{data.ask_size || 'N/A'}</div>
              </div>
            </div>

            <div className="spread-row">
              <span className="label">Spread:</span>
              <span className="value">{getSpread(data.bid_price, data.ask_price)}</span>
            </div>

            <div className="timestamp">
              Updated: {formatTimestamp(data.received_at)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PriceMonitor;
