<!-- ai-generated: 100% - documents the client/server latency gap measurement -->
# Why client p99 differs from server p99

The client measures the full request round trip, while the server histogram starts when the request reaches the
application middleware and stops when the response is ready to leave it. The gap therefore includes network
transit in both directions, proxy scheduling and queueing, and any delay outside the application's measurement
boundary. For the Stretch 2 run, Toxiproxy adds a configured downstream latency toxic with jitter. This delay is
visible to the client but is not part of the server's `/kb/search` duration histogram. The two p99 values are
percentiles of separate latency populations, so subtracting them is an estimate of the additional tail delay,
not a per-request decomposition. The checker re-runs the load through its own proxy and compares the declared
gap to that observation within the published tolerance.
