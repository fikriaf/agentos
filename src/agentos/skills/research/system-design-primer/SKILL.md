---
name: system-design-primer
description: Large-scale system design reference. Use when designing distributed systems, scaling applications, or preparing for system design interviews. Reference concepts like CAP theorem, caching strategies, load balancing, database sharding, and more.
---

# System Design Primer

Comprehensive reference from https://github.com/donnemartin/system-design-primer (344k stars)

## Key Principles

**"Everything is a trade-off"** — Key principle throughout system design.

## Fundamental Trade-offs

| Trade-off | Description |
|-----------|-------------|
| **Performance vs Scalability** | Performance = fast for single user; Scalability = fast under heavy load |
| **Latency vs Throughput** | Latency = time to complete action; Throughput = actions per unit time |
| **Availability vs Consistency** | CAP Theorem — choose 2 of 3 |

## Consistency Patterns

| Pattern | Description | Use Cases |
|---------|-------------|-----------|
| **Weak** | Reads may not see writes | VoIP, gaming |
| **Eventual** | Writes propagate asynchronously | DNS, email |
| **Strong** | Synchronous replication | RDBMS, file systems |

## Availability Metrics

| Availability | Downtime/Year | Downtime/Month |
|--------------|---------------|----------------|
| 99.9% (3 nines) | 8h 46m | 43m 50s |
| 99.99% (4 nines) | 52m 36s | 4m 23s |
| 99.999% (5 nines) | 5m 15s | 26s |

## Core Topics

### Networking & Delivery
- **DNS**: Hierarchical name resolution, A/CNAME/MX/NS records
- **CDN**: Push (upload to CDN) vs Pull (lazy load on first request)
- **Load Balancer**: Layer 4 (transport) vs Layer 7 (application)
- **Reverse Proxy**: Hide backend servers, SSL termination, caching

### Databases
- **RDBMS**: ACID transactions, complex joins
- **NoSQL**: Key-value, document, wide-column, graph stores
- **Scaling**: Replication, Federation, Sharding, Denormalization

### Caching Strategies

```python
# Cache-aside pattern (lazy loading)
def get_user(user_id):
    user = cache.get(f"user.{user_id}")
    if user is None:
        user = db.query("SELECT * FROM users WHERE user_id = ?", user_id)
        cache.set(f"user.{user_id}", json.dumps(user))
    return user
```

| Strategy | Description |
|----------|-------------|
| **Cache-aside** | Lazy loading, application manages |
| **Write-through** | Synchronous write to cache + DB |
| **Write-behind** | Async write to cache, then DB |
| **Refresh-ahead** | Pre-expire popular entries |

## 4-Step System Design Interview Approach

1. **Outline use cases, constraints, assumptions** — Scope problem, ask clarifying questions
2. **Create high-level design** — Sketch main components
3. **Design core components** — Dive into details
4. **Scale the design** — Address bottlenecks: load balancing, caching, sharding

## Reference Tables

### Powers of Two

| Power | Value | Approx |
|-------|-------|--------|
| 10 | 1,024 | 1 KB |
| 20 | 1,048,576 | 1 MB |
| 30 | 1,073,741,824 | 1 GB |
| 40 | 1,099,511,627,776 | 1 TB |

### Latency Reference

| Operation | Latency |
|-----------|---------|
| L1 cache reference | 0.5 ns |
| L2 cache reference | 7 ns |
| Main memory reference | 100 ns |
| SSD random read | 150 μs |
| HDD seek | 10 ms |
| Round trip datacenter | 500 μs |
| Round trip internet | 50 ms |

## Solutions Reference

Located at `/opt/system-design-primer/solutions/system_design/`:

- `mint` — Payment system
- `pastebin` — URL shortener
- `query_cache` — Key-value store
- `twitter` — Twitter timeline/search
- `social_graph` — Social network
- `web_crawler` — Web crawler
- `sales_rank` — Amazon sales ranking
- `scaling_aws` — AWS scalable system
- `template` — Template for new designs

## Additional Resources

- **Real World Architectures**: MapReduce, Spark, BigTable, Cassandra, DynamoDB, HDFS, Kafka
- **Company Engineering Blogs**: Google, Facebook, Netflix, Twitter, Uber, Airbnb