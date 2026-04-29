# Twitter / Social Feed Design

## Problem
Design Twitter with:
- Post tweets (140+ chars)
- Follow/unfollow users
- Home timeline (tweets from followed users)
- Search tweets
- Real-time updates

## 4-Step Approach

### 1. Scope & Constraints
- 300M monthly active users
- 500M tweets/day (6000 tweets/sec)
- 1M queries/sec for timeline
- < 200ms latency for timeline
- Fan-out: each user follows avg 500 people

### 2. High-Level Design

```
User → Web Server → Tweet Service → DB
                              ↓
                        Message Queue
                              ↓
                       Fan-out Service → Cache (Timeline)
```

### 3. Core Approaches

**Push (Fan-out on write):**
```
User posts tweet → Push to all followers' timelines in cache
Pros: Fast reads
Cons: Slow writes for celebrity users, storage blow-up
```

**Pull (Fan-out on read):**
```
User reads timeline → Merge tweets from all followed users
Pros: Fast writes
Cons: Slow reads, need heavy optimization
```

**Hybrid:**
```
Push for normal users, Pull for celebrities (users with >10K followers)
```

### 4. Scaling Challenges

| Challenge | Solution |
|-----------|----------|
| Celebrity tweets | Separate pipeline, don't fan-out to all |
| Timeline storage | Cache per user, TTL 24h |
| Hot users | Rate limiting, separate shards |
| Search | Elasticsearch cluster |

## Key Learnings

- Timeline is personalized — can't just cache all tweets
- Celebrity problem: one tweet → millions of fan-outs
- Hybrid approach balances read/write performance
- Async processing via message queues is critical