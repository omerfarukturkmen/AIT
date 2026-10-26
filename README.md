# AIT

Yapay zekâ destekli egzersiz form analizi. Kullanıcı squat veya şınav
videosunu yükler ya da kamerayla kaydeder; uygulama tekrar sayısını, form
puanını, hataları ve önerileri gösterir.

| Klasör | İçerik |
| --- | --- |
| `lib/` | Flutter uygulaması (Android, iOS, web) |
| `backend/` | FastAPI sunucusu: kimlik doğrulama, video yükleme, analiz geçmişi |
| `ai/` | Poz tespiti ve hareket analizi (MediaPipe); ayrıntılar `ai/README_AI.md` |
| `docs/` | Güvenlik kontrolleri ve proje belgeleri |

Uygulama kimliği: `com.ait.fitness` (Android ve iOS), görünen ad: **AIT**.

## Hızlı başlangıç

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
python ../ai/scripts/download_pose_model.py   # analiz modeli (bir kez)
uvicorn main:app --reload

# 2. Uygulama (ayrı terminalde, proje kökünde)
flutter pub get
flutter run -d chrome
```

Testler: `cd backend && pytest`, `cd ai && pytest`, `flutter test`.

## Kimlik doğrulama

Giriş/kayıt ekranları `lib/features/auth/` altında, backend uçları
`backend/auth.py` içindedir.

### Çalıştırma

```bash
# Backend
cd backend
pip install -r requirements.txt
python ../ai/scripts/download_pose_model.py   # video analizi için model (bir kez)
export AUTH_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
uvicorn main:app --reload

# Uygulama (backend adresi: lib/core/api_config.dart)
flutter run
```

| Ortam değişkeni | Açıklama |
| --- | --- |
| `AUTH_SECRET_KEY` | Oturum token'larını imzalar. Tanımlı değilse her açılışta geçici bir anahtar üretilir ve sunucu yeniden başlayınca tüm oturumlar düşer. Üretimde zorunlu. |
| `ALLOWED_ORIGINS` | Web istemcisi için izin verilen origin'ler (virgülle). Boşsa yalnızca `localhost` / `127.0.0.1` kabul edilir. |
| `MAX_UPLOAD_MB` | Video yükleme sınırı (varsayılan 200). |
| `DATABASE_URL` | Veritabanı adresi (varsayılan `sqlite:///./test.db`). |
| `UPLOAD_FOLDER` | Videoların kaydedildiği klasör (varsayılan `uploaded_videos`). |
| `APP_ENV` | `production` olduğunda `/docs` ve `/openapi.json` kapanır, HSTS başlığı eklenir. |
| `ALLOWED_HOSTS` | API'nin yanıt vereceği alan adları (virgülle); başka `Host` başlıkları 400 alır. |

Flutter tarafında backend adresi: `--dart-define=API_BASE_URL=http://10.0.2.2:8000`
(Android emülatörü) gibi verilir.

### Güvenlik

- `/` ve `/auth/register`, `/auth/login` dışındaki tüm uçlar
  `Authorization: Bearer <token>` ister; aksi halde 401 döner.
- Video sahibi her zaman token'dan belirlenir; istemcinin gönderdiği
  `user_id` yok sayılır. Kullanıcılar yalnızca kendi video ve analizlerini
  görebilir (başkasınınki için 403/404).
- Videolar diskte rastgele (UUID) adla saklanır; istemcinin dosya adı
  kullanılmaz. Boyut sınırı `MAX_UPLOAD_MB` ile belirlenir.
- Videonun içeriği doğrulanır (MP4/MOV/AVI imzası); uzantısı değiştirilmiş
  başka dosyalar 415 ile reddedilir, boş dosya ve çok uzun dosya adı kabul edilmez.
- Hız sınırları (IP veya kullanıcı başına, bellek içi): kayıt 5/saat,
  giriş 20/dk (+ aynı e-posta için 15 dakikada 5 hatalı deneme), video yükleme
  10/10 dk, canlı analiz 120/dk, tüm istekler 300/dk. Aşılınca `429` ve
  `Retry-After` döner. Birden fazla sunucu sürecinde Redis gibi ortak bir depo
  gerekir; ters vekil arkasında `uvicorn --proxy-headers` kullanılmalıdır.
- Oturumlar sunucuda tutulur: çıkış (`POST /auth/logout`) token'ı hemen
  geçersiz kılar, `?all_devices=true` tüm cihazlardan çıkarır. "Beni hatırla"
  seçiliyse oturum 30 gün, değilse 12 saat geçerlidir.
- Hata yanıtları sunucu yolu, istisna metni veya gönderilen veriyi (şifre
  dahil) içermez; uygulama da ham sunucu yanıtını kullanıcıya göstermez.
- Her yanıtta güvenlik başlıkları (`X-Content-Type-Options`, `X-Frame-Options`,
  `Content-Security-Policy`, `Referrer-Policy`, `Cache-Control: no-store`) bulunur.
- Loglara şifre, token veya e-posta yazılmaz; yanlışlıkla gelirse maskelenir.
- Bağımlılıklar sabit sürümlüdür ve `pip-audit` / OSV ile taranmıştır
  (ayrıntılar: `docs/GUVENLIK_KONTROLLERI.md`).
- Oturum token'ı cihazda şifreli saklanır (`flutter_secure_storage`:
  iOS Keychain, Android Keystore, web'de WebCrypto).
- KVKK: Kullanıcı kendi videosunu (`DELETE /videos/{id}`) veya hesabını tüm
  video ve analizleriyle birlikte (`DELETE /auth/me`, Profil → "Hesabımı Sil")
  kalıcı olarak silebilir.
- `backend/test.db` ve `backend/uploaded_videos/` git'e eklenmemelidir.

Uçlar: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`,
`POST /auth/logout`, `DELETE /auth/me` (`Authorization: Bearer <token>`). Şifreler PBKDF2-SHA256
ile hash'lenir.

### Canlıya çıkış (HTTPS)

Token her istekte gönderildiği için canlı ortamda bağlantı **mutlaka HTTPS**
olmalıdır; `http://` yalnızca yerel geliştirme içindir.

1. Backend'i bir TLS sonlandırıcının (Nginx, Caddy veya bulut sağlayıcının
   yük dengeleyicisi) arkasında çalıştırın; `uvicorn` yalnızca `127.0.0.1`
   adresini dinlesin.
2. `APP_ENV=production`, `AUTH_SECRET_KEY`'i güçlü ve gizli bir değerle,
   `ALLOWED_HOSTS`'u API alan adıyla, `ALLOWED_ORIGINS`'i web istemcisinin
   `https://` adresiyle ayarlayın.
3. Uygulamayı `--dart-define=API_BASE_URL=https://api.ornek.com` ile derleyin.
   Android release derlemesi düz `http` trafiğine zaten izin vermez.

### Henüz eksik olanlar

- **Google / Apple ile giriş:** Butonlar hazır, ancak sağlayıcı yapılandırılmadığı
  için kullanıcıya "henüz yapılandırılmadı" mesajı gösterir. Etkinleştirmek için
  `google_sign_in` ve `sign_in_with_apple` paketlerini ekleyin; Google Cloud
  Console'da OAuth istemci kimliklerini (Android SHA-1, iOS URL şeması, web
  istemci kimliği), Apple Developer'da "Sign in with Apple" yetkisini ve Services
  ID'yi oluşturun; backend'e ID token'ı doğrulayan `/auth/google` ve
  `/auth/apple` uçlarını ekleyin; ardından
  `AuthService.signInWithProvider` metodunu güncelleyin.
- **Şifre sıfırlama:** Backend ucu ve e-posta gönderimi yok; "Şifremi unuttum"
  bu durumu açıklayan bir diyalog gösterir.
- **Kullanım Koşulları / Gizlilik Politikası** metinleri henüz eklenmedi.
