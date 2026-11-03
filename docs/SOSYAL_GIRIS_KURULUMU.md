# Google ve Apple ile giriş kurulumu

Kod tarafı hazır: uygulama sağlayıcıdan aldığı kimlik token'ını backend'e
gönderir, backend token'ı sağlayıcının açık anahtarlarıyla doğrular (imza,
yayıncı, hedef kitle, süre) ve AIT oturumu açar. Aynı e-postayla kayıtlı bir
hesap varsa yeni hesap açılmaz, sağlayıcı o hesaba bağlanır.

Aşağıdaki kimlikler girilene kadar butonlar "henüz kullanılamıyor" mesajı
gösterir; hiçbir şey çalışıyormuş gibi görünmez.

Uygulama kimliği: **`com.ait.fitness`** (Android ve iOS).

## 1. Google

1. [Google Cloud Console](https://console.cloud.google.com/) → yeni proje →
   **APIs & Services → OAuth consent screen**: uygulama adı "AIT", destek
   e-postası, gizlilik politikası adresi.
2. **Credentials → Create credentials → OAuth client ID** ile üç istemci:
   - **Web application**: bu, *server client ID* olur.
   - **Android**: paket adı `com.ait.fitness` ve imzalama sertifikasının
     SHA-1 parmak izi (`cd android && ./gradlew signingReport`). Debug ve
     release anahtarları için ayrı ayrı ekleyin.
   - **iOS**: bundle ID `com.ait.fitness`.
3. iOS için `ios/Runner/Info.plist` dosyasına iOS istemcisinin
   *reversed client ID* değerini URL şeması olarak ekleyin
   (`CFBundleURLTypes` → `CFBundleURLSchemes`).
4. Backend: `GOOGLE_CLIENT_IDS=<web istemci kimliği>,<iOS istemci kimliği>`
5. Uygulamayı derlerken:
   ```bash
   flutter run --dart-define=GOOGLE_SERVER_CLIENT_ID=<web istemci kimliği> \
               --dart-define=GOOGLE_IOS_CLIENT_ID=<iOS istemci kimliği>
   ```

Web sürümünde Google girişi Google'ın kendi butonunu gerektirir; şimdilik
yalnızca Android ve iOS'ta etkinleşir.

## 2. Apple

Apple Developer Program üyeliği gerekir.

1. **Certificates, Identifiers & Profiles → Identifiers** → `com.ait.fitness`
   App ID'sinde **Sign in with Apple** yeteneğini açın.
2. Xcode'da `ios/Runner.xcworkspace` → Runner → **Signing & Capabilities →
   + Capability → Sign in with Apple**.
3. Backend: `APPLE_CLIENT_IDS=com.ait.fitness`
4. Uygulamayı derlerken: `--dart-define=APPLE_SIGN_IN_ENABLED=true`

Apple girişi iOS ve macOS'ta etkinleşir. Android ve web için Apple bir
*Services ID* ve geri dönüş adresi ister; ihtiyaç olursa ayrıca kurulmalıdır.

**App Store notu:** iOS'ta Google ile giriş sunan bir uygulamanın, Apple
kuralları gereği gizliliği koruyan eşdeğer bir giriş seçeneği de sunması
gerekir; "Apple ile giriş" bunu karşılar.

## 3. Doğrulama

- Backend testleri gerçek doğrulama yolunu sahte anahtarlarla dener:
  `cd backend && pytest tests/test_product_features.py -k google`.
- Kimlikleri girdikten sonra gerçek cihazda giriş yapıp Profil'de
  e-postanın "Doğrulandı" göründüğünü kontrol edin.
