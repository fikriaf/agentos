# Pastebin / URL Shortener Design

## Problem
Design a URL shortener like Bit.ly with:
- Given a URL, generate a short URL
- Given a short URL, redirect to original URL
- Optional: analytics, custom URLs, deletion

## 4-Step Approach

### 1. Scope & Constraints
- 100M URLs/month
- 10:1 read/write ratio (10B redirections/month)
- Latency < 100ms for redirections
- 99.9% availability

### 2. High-Level Design

```
User → API Server → DB (write)
                      ↓
                   Cache
                      ↓
User ← API Server ← Cache ← DB (read)
```

### 3. Core Components

**Hash Generation:**
- Use MD5/SHA256 of URL, take first 7 chars
- Or use base62 encoding
- Handle collisions with lookup table

**Database Schema:**
```sql
urls (
  id: BIGINT PRIMARY KEY,
  short_url: VARCHAR(16) UNIQUE,
  original_url: TEXT NOT NULL,
  created_at: TIMESTAMP,
  is_active: BOOLEAN
)
```

### 4. Scaling

| Bottleneck | Solution |
|------------|----------|
| Read-heavy | Redis cache for hot URLs |
| Hash collisions | Check DB, regenerate or use counter |
| Single DB | Read replicas, eventually sharding |
| Sequential IDs | Flake IDs or random 64-bit |

## Key Learnings

- Pre-compute short URLs to avoid "hot" keys
- Use consistent hashing for sharding
- Rate limiting on API endpoints
- Analytics: async write to separate service