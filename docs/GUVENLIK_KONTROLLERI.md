# Güvenlik Kontrolleri

AIT Fitness uygulaması (Flutter) ve backend'i (FastAPI) için yapılan güvenlik
kontrolleri. Her madde için bulunan sorun, yapılan düzeltme ve bunu doğrulayan
otomatik test listelenmiştir.

**Durum (22.10.2026):** 12 kontrolün 12'si tamamlandı.
Backend 63, AI modülü 540, Flutter 33 test geçiyor; ayrıca gerçek backend'e
karşı uçtan uca API ve tarayıcı testleri çalıştırıldı.

| Öncelik | Alan | Kontrol | Durum |
| --- | --- | --- | --- |
| P0 | Kimlik doğrulama | Yetkisiz kullanıcı sisteme girebiliyor mu? | ✅ Engellendi |
| P0 | API güvenliği | API uç noktalarına izinsiz erişilebiliyor mu? | ✅ Engellendi |
| P0 | Veri güvenliği | Kullanıcı bilgileri ve videolar korunuyor mu? | ✅ Korunuyor |
| P0 | Şifre ve API anahtarları | Kodda gizli anahtar var mı? | ✅ Yok, geçmiş temizlendi |
| P1 | Dosya yükleme | Zararlı/uygunsuz dosyalar engelleniyor mu? | ✅ Engelleniyor |
| P1 | Girdi doğrulama | Hatalı/kötü amaçlı veriler kontrol ediliyor mu? | ✅ Kontrol ediliyor |
| P1 | Rate limiting | Otomatik istekler sınırlanıyor mu? | ✅ Sınırlanıyor |
| P1 | Oturum güvenliği | Token ve oturum sonlandırma güvenli mi? | ✅ Güvenli |
| P1 | Bağımlılık güvenliği | Paketlerde bilinen açık var mı? | ✅ Bilinen açık yok |
| P2 | Hata yönetimi | Hata mesajları hassas bilgi sızdırıyor mu? | ✅ Sızdırmıyor |
| P2 | Web güvenliği | CORS, HTTPS ve güvenlik başlıkları doğru mu? | ✅ Doğru (HTTPS dağıtımda) |
| P2 | Log güvenliği | Loglarda parola, token veya kişisel veri var mı? | ✅ Yok |

Testler: `backend/tests/test_auth.py`, `test_api_security.py`,
`test_security_p1_p2.py`, `test_ai_analyzer.py`; Flutter tarafında `test/`.

---

## P0 — Kimlik doğrulama

- **Bulunan:** Şifreler veritabanında düz metin saklanıyordu; giriş bilgileri
  URL'de gönderiliyordu; video yükleme isteği gönderilen `user_id`'ye
  güveniyordu (herkes başkası adına yükleyebiliyordu).
- **Yapılan:** Şifreler PBKDF2-SHA256 (390.000 tur, rastgele tuz) ile
  hash'leniyor. Giriş/kayıt JSON gövdesiyle yapılıyor. Kullanıcı kimliği her
  zaman imzalı oturum token'ından alınıyor. Bilinmeyen e-posta ve yanlış
  şifreye aynı yanıt veriliyor.
- **Test:** `test_register_hashes_password_and_returns_session`,
  `test_login_with_correct_and_wrong_password`,
  `test_upload_owner_comes_from_token_not_form`.

## P0 — API güvenliği

- **Bulunan:** `/`, kayıt ve giriş dışındaki hiçbir uç oturum istemiyordu;
  URL'deki sayı değiştirilerek başkasının video ve analizleri okunabiliyordu;
  `/analysis-history` tüm kullanıcıların verisini döndürüyordu.
- **Yapılan:** Tüm veri uçları `Authorization: Bearer <token>` istiyor (yoksa
  401). Kullanıcı yalnızca kendi verisini görüyor; başkasınınki için 403/404.
- **Test:** `test_endpoints_reject_missing_or_forged_token` (10 uç),
  `test_users_cannot_read_each_others_data`.

## P0 — Veri güvenliği

- **Bulunan:** Videolar istemcinin verdiği dosya adıyla kaydediliyordu
  (`../../x.mp4` ile klasör dışına yazılabiliyordu, aynı adlı dosyalar
  birbirinin üzerine yazılıyordu). Kullanıcı verisini silmenin yolu yoktu.
- **Yapılan:** Videolar rastgele (UUID) adla saklanıyor. KVKK için kullanıcı
  tek bir videosunu (`DELETE /videos/{id}`) veya hesabını tüm verisiyle
  (`DELETE /auth/me`, Profil → "Hesabımı Sil") silebiliyor. Token cihazda
  şifreli saklanıyor (`flutter_secure_storage`). Çıkışta analiz geçmişi
  temizleniyor.
- **Test:** `test_upload_filename_cannot_escape_folder`,
  `test_only_owner_can_delete_video_and_file_is_removed`,
  `test_delete_account_erases_all_user_data`, `auth_store_test.dart`.

## P0 — Şifre ve API anahtarları

- **Bulunan:** Kodda API anahtarı yoktu. Ancak `backend/test.db` (bir
  kullanıcının düz metin şifresiyle) ve gerçek bir video git'e eklenip
  GitHub'a gönderilmişti.
- **Yapılan:** İki dosya tüm git geçmişinden silindi (`git filter-repo`,
  repo sahibinin onayıyla force-push). Tüm geçmiş anahtar ve şifre kalıpları
  için tarandı, başka bulgu çıkmadı. İmzalama anahtarı `AUTH_SECRET_KEY`
  ortam değişkeninden okunuyor.
- **Açık kalan:** Eski kopyası olan ekip üyeleri depoyu yeniden klonlamalı;
  sızan şifre başka yerde kullanılıyorsa değiştirilmeli.

## P1 — Dosya yükleme

- **Bulunan:** Yalnızca dosya uzantısına bakılıyordu; `.mp4` adı verilmiş bir
  `.exe` kabul ediliyordu. Boş dosya geç fark ediliyordu.
- **Yapılan:** Dosyanın içeriği kontrol ediliyor: MP4/MOV için ISO-BMFF
  kutusu (`ftyp`, `moov`…), AVI için `RIFF…AVI` imzası. Uzantı ile içerik
  uyuşmazsa 415. Boş dosya, 255 karakterden uzun dosya adı ve
  `MAX_UPLOAD_MB` (varsayılan 200 MB) üstü reddediliyor; reddedilen dosya
  diskten siliniyor. Video ayrıca OpenCV ile açılarak doğrulanıyor.
- **Test:** `test_rejects_non_video_uploads` (exe, betik, sahte AVI, boş, uzun
  ad, PDF), `test_rejected_upload_leaves_no_file_behind`,
  `test_upload_size_limit`.

## P1 — Girdi doğrulama

- **Bulunan:** Ad ve e-posta için uzunluk sınırı yoktu; canlı analizdeki
  `frame_data` sınırsızdı.
- **Yapılan:** Ad en fazla 100, e-posta 254, şifre 128 karakter; addaki kontrol
  karakterleri ve harf içermeyen adlar reddediliyor. Hareket türü yalnızca
  `squat` / `push-up`. `frame_data` en fazla 1 MB. Tüm tipler şema ile
  doğrulanıyor. Uygulamadaki alanlar aynı sınırları uyguluyor. Veritabanı
  erişimi SQLAlchemy ile parametreli (SQL enjeksiyonu yok).
- **Test:** `test_register_rejects_malformed_input`, `test_wrong_types_are_rejected`,
  `test_live_analysis_limits_frame_size_and_exercise`,
  `text fields enforce their maximum length`.

## P1 — Rate limiting

- **Bulunan:** Yalnızca hatalı şifre denemesi sınırlıydı; kayıt, video
  yükleme (en pahalı işlem) ve analiz sınırsızdı.
- **Yapılan:** Kayıt 5/saat (IP), giriş 20/dk (IP) + aynı e-posta için
  15 dakikada 5 hatalı deneme, video yükleme 10/10 dk (kullanıcı), canlı
  analiz 120/dk (kullanıcı), tüm istekler 300/dk (IP). Aşılınca 429 ve
  `Retry-After`.
- **Sınırlama:** Sayaçlar bellekte tutulur; birden fazla sunucu sürecinde
  Redis gibi ortak bir depo gerekir. Ters vekil arkasında
  `uvicorn --proxy-headers` ile gerçek istemci IP'si alınmalıdır.
- **Test:** `test_registration_is_rate_limited_per_ip`,
  `test_uploads_are_rate_limited_per_user`, `test_global_request_limit`,
  `test_login_locks_after_repeated_failures`.

## P1 — Oturum güvenliği

- **Bulunan:** Token iptal edilemiyordu; çıkış yapılsa da 30 gün geçerli
  kalıyordu.
- **Yapılan:** Her oturum sunucuda kayıtlı (rastgele `jti`). Çıkış
  (`POST /auth/logout`) token'ı anında geçersiz kılıyor; `?all_devices=true`
  tüm cihazlardan çıkarıyor; hesap silinince tüm oturumlar siliniyor.
  "Beni hatırla" seçili değilse oturum 12 saat, seçiliyse 30 gün. İmza
  HMAC-SHA256, karşılaştırmalar sabit zamanlı. Uygulama çıkışta token'ı
  sunucuda da iptal ediyor (çevrimdışıyken yerel çıkış yine çalışır).
- **Test:** `test_logout_revokes_only_that_token`, `test_logout_all_devices`,
  `test_session_lifetime_follows_remember_me`,
  `test_expired_server_session_is_rejected`,
  `test_signed_token_without_server_session_is_rejected`,
  `sign out revokes the token on the server`.

## P1 — Bağımlılık güvenliği

- **Bulunan:** Backend paketleri sürüm sabitlenmeden kuruluyordu.
  `pip-audit`, mediapipe üzerinden gelen `protobuf 4.25.9` paketinde
  PYSEC-2026-1805 açığı buldu. Backend mediapipe'ı 0.10.21'e sabitliyordu,
  AI modülü ise 0.10.35 istiyordu (uyumsuzluk).
- **Yapılan:** `backend/requirements.txt` sabit sürümlü; mediapipe AI
  modülüyle aynı sürüme (0.10.35) getirildi, `protobuf` 7.36.2'ye yükseltildi.
  `pip-audit`: **bilinen açık yok**. Flutter tarafında 101 paket OSV
  veritabanında tarandı: **bilinen açık yok**; izin verilen aralıktaki yama
  güncellemeleri alındı.
- **Bekleyen (açık değil, sürüm güncellemesi):** `fl_chart` 1.x,
  `file_picker` 13, `camera` 0.12 büyük sürümleri API değişikliği
  içerdiğinden ayrıca denenmeli.
- **Yeniden tarama:** `pip-audit -r backend/requirements.txt`; Flutter için
  `flutter pub outdated` ve OSV taraması.

## P2 — Hata yönetimi

- **Bulunan:** Analiz hataları sunucunun dosya yolunu
  (`Video dosyasi bos: C:\…\uploaded_videos\…`) ve ham istisna metnini
  istemciye döndürüyor ve veritabanına yazıyordu. Başarılı analiz yanıtı da
  `details.video_path` alanında sunucu yolunu içeriyordu. Doğrulama hataları
  (422) gönderilen veriyi, şifre dahil, geri yansıtıyordu. Uygulama ham sunucu
  yanıtını kullanıcıya gösteriyordu.
- **Yapılan:** İstemciye yalnızca güvenli, Türkçe mesajlar dönüyor; ayrıntı
  sunucu loguna yazılıyor. 422 yanıtı yalnızca hatalı alan adlarını
  içeriyor. Beklenmeyen hatalar genel bir 500 mesajı döndürüyor. Uygulama
  sunucu hatalarında (5xx) ve JSON olmayan yanıtlarda genel mesaj gösteriyor.
- **Test:** `test_analysis_errors_hide_server_paths`,
  `test_unhandled_errors_return_generic_message`,
  `test_validation_errors_do_not_echo_submitted_values`,
  `test_real_video_reports_reps_without_server_paths`,
  `api_error_handling_test.dart`.

## P2 — Web güvenliği

- **CORS:** Varsayılan olarak yalnızca `localhost`; canlıda `ALLOWED_ORIGINS`.
  Kimlik bilgisi (cookie) gönderimi kapalı.
- **Güvenlik başlıkları:** `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Content-Security-Policy: default-src 'none'`,
  `Referrer-Policy: no-referrer`, `Permissions-Policy`,
  `Cache-Control: no-store` her yanıtta (hata yanıtları dahil).
- **Canlı ortam (`APP_ENV=production`):** `/docs` ve `/openapi.json`
  kapanıyor, HSTS ekleniyor; `ALLOWED_HOSTS` dışındaki `Host` başlıkları 400.
- **HTTPS:** Uygulama kodu tarafından değil, dağıtımda sağlanır (TLS
  sonlandırıcı arkasında çalıştırma; README → "Canlıya çıkış"). Android
  release derlemesi düz HTTP'ye izin vermiyor; iOS ATS de varsayılan olarak
  engeller.
- **Test:** `test_security_headers_on_success_and_error_responses`,
  `test_production_mode_hardening`, `test_cors_only_allows_local_origins_by_default`.

## P2 — Log güvenliği

- **İncelenen:** Backend, AI analizörü ve uygulama logları.
- **Durum:** Şifre, token ve e-posta hiçbir yerde loglanmıyor; analizör artık
  tam dosya yolu yerine yalnızca dosya adını yazıyor. Ek önlem olarak log
  filtresi `Bearer …`, `password`, `access_token` değerlerini maskeliyor.
  Başarısız girişlerde güvenlik amacıyla yalnızca IP adresi loglanıyor.
- **Test:** `test_logs_never_contain_passwords_or_tokens`,
  `test_redaction_filter_masks_secrets`; uçtan uca testte gerçek sunucu logu
  da tarandı.

---

## Bu çalışma sırasında bulunan ve düzeltilen diğer hatalar

- **Video analizi her zaman 0 tekrar döndürüyordu:** backend, AI modülünün
  eski çıktı alanlarını okuyordu. Aynı video artık 0 tekrar / 44 puan yerine
  doğru şekilde 2 tekrar / 90 puan veriyor.
- **Analiz bu klasörde hiç çalışmıyordu:** MediaPipe, Türkçe karakter içeren
  Windows yollarındaki (`Masaüstü`) model dosyasını açamıyordu; model artık
  bellek üzerinden yükleniyor.

## Kalan riskler ve öneriler

- Rate limit ve hatalı giriş sayaçları tek süreçlidir (çoklu sunucu için Redis).
- Şifre sıfırlama ve Google/Apple girişi henüz yok (README → "Henüz eksik olanlar").
- `fl_chart`, `file_picker`, `camera` büyük sürüm güncellemeleri ayrıca test edilmeli.
- Bağımlılık taraması düzenli tekrarlanmalı (ör. her sürüm öncesi).
