import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import ws from "../../src/api/ws";

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState = MockWebSocket.CONNECTING;

  onopen: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;

  send = vi.fn();
  close = vi.fn(() => {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  });

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }
}

declare global {
  var WebSocket: typeof MockWebSocket;
}

beforeEach(() => {
  MockWebSocket.instances = [];
  globalThis.WebSocket = MockWebSocket as any;
  vi.useFakeTimers();
  ws.disconnect();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("ws (singleton WebSocket client)", () => {
  it("constructs WebSocket with correct URL and adds token to query", async () => {
    const token = "abc123";

    const connectPromise = ws.connect(token);

    const socket = MockWebSocket.instances[0];
    expect(socket.url).toContain("token=abc123");

    socket.readyState = MockWebSocket.OPEN;
    socket.onopen?.();

    await connectPromise;
  });

  it("does not recreate the connection if it is already OPEN/CONNECTING", async () => {
    const first = ws.connect("token1");

    const socket = MockWebSocket.instances[0];
    socket.readyState = MockWebSocket.OPEN;
    socket.onopen?.();
    await first;

    const second = ws.connect("token2");
    await second;

    expect(MockWebSocket.instances).toHaveLength(1);
  });

  it("notifies subscribers on onmessage and ignores errors in callbacks", async () => {
    const connectPromise = ws.connect();
    const socket = MockWebSocket.instances[0];

    socket.readyState = MockWebSocket.OPEN;
    socket.onopen?.();
    await connectPromise;

    const cb1 = vi.fn(() => {
      throw new Error("boom");
    });
    const cb2 = vi.fn();

    ws.subscribe(cb1);
    ws.subscribe(cb2);

    const payload = { hello: "world" };
    socket.onmessage?.({ data: JSON.stringify(payload) });

    expect(cb1).toHaveBeenCalledWith(payload);
    expect(cb2).toHaveBeenCalledWith(payload);
  });

  it("unsubscribe removes the callback from the set", async () => {
    const connectPromise = ws.connect();
    const socket = MockWebSocket.instances[0];
    socket.readyState = MockWebSocket.OPEN;
    socket.onopen?.();
    await connectPromise;

    const cb = vi.fn();
    const unsubscribe = ws.subscribe(cb);

    unsubscribe();

    socket.onmessage?.({ data: JSON.stringify({ x: 1 }) });

    expect(cb).not.toHaveBeenCalled();
  });

  it("send waits until the connection becomes OPEN and sends JSON", async () => {
    const sendPromise = ws.send({ msg: "hello" });

    const socket = MockWebSocket.instances[0];
    expect(socket.readyState).toBe(MockWebSocket.CONNECTING);

    socket.readyState = MockWebSocket.OPEN;
    socket.onopen?.();

    const ok = await sendPromise;
    expect(ok).toBe(true);
    expect(socket.send).toHaveBeenCalledWith(JSON.stringify({ msg: "hello" }));
  });

  it("send returns false if the socket closes after connect", async () => {
    const connectPromise = ws.connect();
    const socket = MockWebSocket.instances[0];
    socket.readyState = MockWebSocket.OPEN;
    socket.onopen?.();
    await connectPromise;

    socket.readyState = MockWebSocket.CLOSED;

    const ok = await ws.send({ msg: "nope" });
    expect(ok).toBe(false);
  });

  it("disconnect stops reconnection and closes the socket", async () => {
    const connectPromise = ws.connect();
    const socket = MockWebSocket.instances[0];
    socket.readyState = MockWebSocket.OPEN;
    socket.onopen?.();
    await connectPromise;

    ws.disconnect();

    expect(socket.close).toHaveBeenCalled();
  });

  it("scheduleReconnect reconnects with backoff when the connection closes", async () => {
    const connectPromise = ws.connect();
    const firstSocket = MockWebSocket.instances[0];
    firstSocket.readyState = MockWebSocket.OPEN;
    firstSocket.onopen?.();
    await connectPromise;

    firstSocket.close(); 

    expect(MockWebSocket.instances).toHaveLength(1);

    vi.advanceTimersByTime(1000);

    expect(MockWebSocket.instances.length).toBeGreaterThanOrEqual(2);
  });
});
