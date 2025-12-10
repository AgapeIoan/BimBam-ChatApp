type WSCallback = (envelope: any) => void;

class WsClient {
  private ws: WebSocket | null = null;
  private subscribers: Set<WSCallback> = new Set();
  private reconnectAttempt = 0;
  private url: string;
  private token?: string;
  private shouldReconnect = true;
  private openPromise: Promise<void> | null = null;

  constructor(url?: string) {
    // default to same host and /ws endpoint; override by passing url
    if (url) {
      this.url = url;
    } else {
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      this.url = `${protocol}://${window.location.host}/ws`;
    }
  }

  /**
   * Connect the websocket. If already connecting/open it no-ops.
   * Optionally pass a token which will be added as ?token=... to the URL.
   */
  connect(token?: string): Promise<void> {
    this.token = token;

    // if already open or connecting, return existing promise
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return this.openPromise ?? Promise.resolve();
    }

    this.shouldReconnect = true;

    let url = this.url;
    if (this.token) {
      const sep = url.includes("?") ? "&" : "?";
      url = `${url}${sep}token=${encodeURIComponent(this.token)}`;
    }

    // create new promise that resolves when onopen fires
    this.openPromise = new Promise((resolve) => {
      try {
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          this.reconnectAttempt = 0;
          resolve();
        };

        this.ws.onmessage = (ev) => {
          try {
            const env = JSON.parse(ev.data);
            // notify subscribers (defensive copy)
            for (const cb of Array.from(this.subscribers)) {
              try {
                cb(env);
              } catch (err) {
                // swallow subscriber errors — they should handle their own errors
                // eslint-disable-next-line no-console
                console.warn("ws subscriber callback error", err);
              }
            }
          } catch (err) {
            // eslint-disable-next-line no-console
            console.warn("ws: failed to parse message", err);
          }
        };

        this.ws.onclose = () => {
          this.ws = null;
          if (this.shouldReconnect) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = () => {
          // do not reject the openPromise here; onclose will handle reconnect
        };
      } catch (err) {
        // fallback: schedule reconnect attempts
        this.ws = null;
        this.scheduleReconnect();
        resolve(); // resolve to avoid hanging callers; they should check readiness if needed
      }
    });

    return this.openPromise;
  }

  private scheduleReconnect() {
    this.reconnectAttempt++;
    // exponential backoff with cap
    const timeout = Math.min(1000 * 2 ** (this.reconnectAttempt - 1), 30_000);
    setTimeout(() => {
      if (this.shouldReconnect) {
        // ignore connect errors here
        // eslint-disable-next-line @typescript-eslint/no-floating-promises
        this.connect(this.token).catch(() => {});
      }
    }, timeout);
  }

  /**
   * Stop reconnecting and close socket if any.
   */
  disconnect(): void {
    this.shouldReconnect = false;
    if (this.ws) {
      try {
        this.ws.close();
      } catch {
        // ignore
      }
      this.ws = null;
    }
    this.openPromise = null;
    this.reconnectAttempt = 0;
  }

  /**
   * Subscribe to incoming envelopes.
   * Returns an unsubscribe function that returns void (important for useEffect cleanup).
   */
  subscribe(cb: WSCallback): () => void {
    this.subscribers.add(cb);
    return () => {
      // intentionally ignore the boolean returned by Set.delete; we return void
      this.subscribers.delete(cb);
    };
  }

  /**
   * Send a message (JSON serialized).
   * Returns true on success, false otherwise.
   */
  async send(message: any): Promise<boolean> {
    // best-effort: wait until connection established
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      try {
        if (this.openPromise) {
          await this.openPromise;
        } else {
          await this.connect(this.token);
        }
      } catch {
        // ignore - will attempt to send anyway below
      }
    }

    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      // not connected
      // eslint-disable-next-line no-console
      console.warn("ws: not connected, cannot send");
      return false;
    }

    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn("ws send failed", err);
      return false;
    }
  }
}

// Export a default singleton client with simple API
const defaultClient = new WsClient();

export default {
  connect: (token?: string) => defaultClient.connect(token),
  disconnect: () => defaultClient.disconnect(),
  subscribe: (cb: WSCallback) => defaultClient.subscribe(cb),
  send: (message: any) => defaultClient.send(message),
};
