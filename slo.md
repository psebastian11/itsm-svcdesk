---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: 30d
  slis:
    availability:
      objective: 0.99
      good: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code!~"5.."}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.01, minutes: 432}
    latency:
      objective: 0.99
      threshold_seconds: 0.25
      good: 'sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.25"}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.01, minutes: 432}
  alerts:
    - {alert: KbSearchAvailabilityBurnFast, sli: availability, burn_rate: 14.4, long_window: 1h, short_window: 5m}
    - {alert: KbSearchAvailabilityBurnSlow, sli: availability, burn_rate: 6, long_window: 6h, short_window: 30m}
---
<!-- ai-generated: 100% - objectives and budgets selected from the Lab 3 SLO requirements -->

# SLO for `GET /kb/search`

## Availability

The service objective is 99% successful responses over 30 days. The availability SLI counts responses that are
not 5xx as good; a failure from `kb-index` is returned as 502 and therefore consumes budget. The 1% allowance is
intentionally greater than zero because the upstream's seeded failures are outside this service's control, but
still makes sustained dependency outages visible. Its budget is 0.01 x 43,200 = 432 minutes.

## Latency

The latency SLI counts searches completed within 250 ms. In the measured run, p50 was 38.2 ms, p95 64.8 ms,
and p99 218.4 ms, with the slow tail reaching 254.3 ms at p99.99. The threshold therefore covers the ordinary
distribution and sits just above p99, while retaining visibility into the slow mode. The 99% objective is
intentionally aligned with the measured p99 rather than promising that the slow tail never occurs. The 250 ms
boundary is explicit in the histogram, so this SLI counts requests rather than interpolating. Its 1% error budget
is 432 minutes.

## Alerts

| alert | SLI | burn rate | long / short window | budget spent when it fires | severity: page or chat |
|---|---|---:|---|---|---|
| KbSearchAvailabilityBurnFast | availability | 14.4 | 1h / 5m | 2% of the 30-day budget | P1 page |
| KbSearchAvailabilityBurnSlow | availability | 6 | 6h / 30m | 5% of the 30-day budget | P2 chat |

The fast alert pages because the budget is being consumed rapidly and should be investigated while users are
affected. The slower alert goes to chat to avoid waking someone for a less urgent trend; its long window provides
time to investigate before a substantial share of the budget is spent.

## Buckets

The histogram uses finite boundaries from 20 ms to 994 ms, spaced at approximately 15% intervals, with an
additional explicit 250 ms boundary for the latency SLI. The measured p99 of 218.4 ms lies in (214, 246] ms,
a 32 ms bucket that is 14.7% of p99. This resolves the observed slow mode while leaving adjacent boundaries
around it to retain useful resolution if the profile shifts. The measured histogram p99 was 220.2 ms, within
1% of the client-side measurement.
