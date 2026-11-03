# Sunucuya dağıtım

`deploy/` klasörü, backend'i HTTPS ile yayınlamak için hazır bir yapı içerir:
API (FastAPI), PostgreSQL ve sertifikayı otomatik alan Caddy.

> **Not:** Bu dosyalar Docker kurulu olmayan bir ortamda yazıldı ve henüz
> çalıştırılarak denenmedi. İlk kurulumda adımları bir test sunucusunda
> doğrulayın.

## Gereksinimler

- Docker ve Docker Compose kurulu bir Linux sunucu (en az 2 vCPU, 4 GB RAM;
  video analizi CPU kullanır).
- API için bir alan adı (ör. `api.ornek.com`) ve bu adın sunucuya yönlenmesi.
- E-posta gönderimi için bir SMTP hesabı (şifre sıfırlama ve doğrulama kodları).

## Kurulum

```bash
git clone <repo> && cd AIT
cp deploy/.env.example deploy/.env      # değerleri doldurun
docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d --build
curl https://api.ornek.com/              # {"message": "Backend çalışıyor"}
```

Veritabanı şeması ilk açılışta Alembic ile otomatik oluşturulur. Videolar
`uploads` biriminde tutulur ve `VIDEO_RETENTION_DAYS` (varsayılan 30) gün
sonra silinir.

## Uygulamayı canlı API'ye bağlama

```bash
flutter build apk --release --dart-define=API_BASE_URL=https://api.ornek.com
flutter build ipa --release --dart-define=API_BASE_URL=https://api.ornek.com
```

## İşletim notları

- **Yedekleme:** `pgdata` ve `uploads` birimlerini düzenli yedekleyin
  (ör. her gece `pg_dump`).
- **Ölçekleme:** Analizler API sürecinin içindeki iş parçacıklarında çalışır
  (`ANALYSIS_WORKERS`, varsayılan 2). Birden fazla API kopyası çalıştırmak
  için analizi bir iş kuyruğuna (Celery/RQ) ve hız sınırlarını Redis'e taşıyın.
- **Güncelleme:** `git pull` → `docker compose ... up -d --build`. Bekleyen
  veritabanı değişiklikleri açılışta uygulanır.
- **Gizli değerler:** `deploy/.env` git'e eklenmez; `AUTH_SECRET_KEY`
  değiştirilirse tüm oturumlar kapanır.
