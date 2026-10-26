import '../core/legal_info.dart';

/// A legal document as headed sections. Kept in code (not ARB) because the
/// texts are long and versioned together.
typedef LegalSection = (String heading, String body);

const _c = LegalInfo.controllerName;
const _e = LegalInfo.contactEmail;

final Map<String, List<LegalSection>> privacyPolicy = {
  'tr': [
    (
      'Kapsam',
      'Bu politika, AIT uygulamasını kullanırken hangi kişisel verilerinin işlendiğini, neden işlendiğini ve haklarını açıklar. Veri sorumlusu: $_c.',
    ),
    (
      'Topladığımız veriler',
      '• Hesap bilgileri: ad soyad, e-posta adresi ve şifrenin geri döndürülemez özeti (şifrenin kendisi saklanmaz).\n'
          '• Egzersiz videoları: analiz için yüklediğin ya da kaydettiğin videolar. Videolar vücut görüntünü içerir.\n'
          '• Analiz sonuçları: form puanı, tekrar sayısı, açı ölçümleri ve tespit edilen form hataları.\n'
          '• Güvenlik kayıtları: hatalı giriş denemelerinde IP adresi.\n'
          '• Google veya Apple ile giriş yaparsan bu sağlayıcının doğruladığı e-posta adresi, adın ve hesap kimliği.',
    ),
    (
      'Cihazında kalan veriler',
      'Kilo, boy, hedef kilo ve vücut ölçüleri yalnızca cihazında saklanır, sunucularımıza gönderilmez. Oturum anahtarın cihazında şifreli olarak tutulur.',
    ),
    (
      'Verileri ne için kullanıyoruz',
      'Hesabını yönetmek, videolarını analiz edip sonuçları sana göstermek, analiz geçmişini saklamak, şifre sıfırlama ve e-posta doğrulama kodlarını göndermek ve hizmeti kötüye kullanıma karşı korumak için. Verilerini reklam amacıyla kullanmayız ve satmayız.',
    ),
    (
      'Saklama süreleri',
      'Videolar yüklendikten 30 gün sonra otomatik olarak silinir. Analiz sonuçları ve hesap bilgileri hesabını silene kadar saklanır. Doğrulama kodları 15 dakika geçerlidir.',
    ),
    (
      'Paylaşım',
      'Verilerin yalnızca hizmeti çalıştırmak için gereken altyapı sağlayıcılarıyla (sunucu barındırma ve e-posta gönderimi) ve yasal zorunluluk hâlinde yetkili makamlarla paylaşılır.',
    ),
    (
      'Hakların',
      'Verilerine erişme, düzeltme ve silme hakkına sahipsin. Hesabını ve tüm verilerini uygulamada Ayarlar → Hesabımı sil ile kalıcı olarak silebilirsin. Diğer talepler için: $_e.',
    ),
  ],
  'en': [
    (
      'Scope',
      'This policy explains which personal data is processed when you use the AIT app, why, and what your rights are. Data controller: $_c.',
    ),
    (
      'Data we collect',
      '• Account details: full name, e-mail address and a one-way hash of your password (the password itself is never stored).\n'
          '• Exercise videos: videos you upload or record for analysis. They contain images of your body.\n'
          '• Analysis results: form score, repetition count, angle measurements and detected form issues.\n'
          '• Security records: your IP address after failed sign-in attempts.\n'
          '• If you sign in with Google or Apple: the e-mail address, name and account ID verified by that provider.',
    ),
    (
      'Data that stays on your device',
      'Weight, height, target weight and body measurements are stored only on your device and are not sent to our servers. Your session key is stored encrypted on your device.',
    ),
    (
      'How we use your data',
      'To manage your account, analyze your videos and show you the results, keep your analysis history, send password reset and e-mail verification codes, and protect the service from abuse. We don\'t use your data for advertising and we don\'t sell it.',
    ),
    (
      'Retention',
      'Videos are deleted automatically 30 days after upload. Analysis results and account details are kept until you delete your account. Verification codes are valid for 15 minutes.',
    ),
    (
      'Sharing',
      'Your data is shared only with infrastructure providers needed to run the service (server hosting and e-mail delivery) and with authorities where required by law.',
    ),
    (
      'Your rights',
      'You can access, correct and delete your data. You can permanently delete your account and all of its data in Settings → Delete account. For other requests: $_e.',
    ),
  ],
};

final Map<String, List<LegalSection>> kvkkNotice = {
  'tr': [
    (
      'Veri sorumlusu',
      '6698 sayılı Kişisel Verilerin Korunması Kanunu ("KVKK") uyarınca kişisel verileriniz veri sorumlusu sıfatıyla $_c tarafından aşağıda açıklanan kapsamda işlenmektedir.',
    ),
    (
      'İşlenen kişisel veriler',
      'Kimlik (ad soyad), iletişim (e-posta), müşteri işlem (analiz sonuçları), görsel kayıt (egzersiz videoları) ve işlem güvenliği (IP adresi, oturum kayıtları) verileri.',
    ),
    (
      'İşleme amaçları ve hukuki sebepler',
      'Üyelik sözleşmesinin kurulması ve ifası (KVKK m.5/2-c), hizmetin sunulması için analiz yapılması, bilgi güvenliğinin sağlanması ve hukuki yükümlülüklerin yerine getirilmesi (m.5/2-ç) ile veri sorumlusunun meşru menfaati (m.5/2-f). Videolarındaki görüntüler yalnızca hareket analizi için işlenir.',
    ),
    (
      'Aktarım',
      'Kişisel verileriniz, hizmetin sunulması için gerekli barındırma ve e-posta altyapı sağlayıcılarına ve talep hâlinde yetkili kamu kurumlarına KVKK m.8 ve m.9\'daki şartlara uygun olarak aktarılabilir.',
    ),
    (
      'Toplama yöntemi',
      'Verileriniz uygulama üzerinden elektronik ortamda, sizin tarafınızdan sağlanarak ve kullanım sırasında otomatik yollarla toplanır.',
    ),
    (
      'Haklarınız (KVKK m.11)',
      'Kişisel verilerinizin işlenip işlenmediğini öğrenme, bilgi talep etme, amacına uygun kullanılıp kullanılmadığını öğrenme, aktarıldığı üçüncü kişileri bilme, eksik veya yanlış işlenmişse düzeltilmesini, silinmesini veya yok edilmesini isteme, itiraz etme ve zararın giderilmesini talep etme haklarına sahipsiniz. Başvurularınızı $_e adresine iletebilirsiniz.',
    ),
  ],
  'en': [
    (
      'Data controller',
      'Under Turkish Personal Data Protection Law No. 6698 ("KVKK"), your personal data is processed by $_c as data controller, as described below.',
    ),
    (
      'Personal data processed',
      'Identity (full name), contact (e-mail), customer transaction (analysis results), visual records (exercise videos) and transaction security (IP address, session records) data.',
    ),
    (
      'Purposes and legal grounds',
      'Establishing and performing the membership agreement (KVKK Art. 5/2-c), analyzing videos to provide the service, ensuring information security and meeting legal obligations (Art. 5/2-ç), and the controller\'s legitimate interest (Art. 5/2-f). Images in your videos are processed only for movement analysis.',
    ),
    (
      'Transfers',
      'Your data may be transferred to hosting and e-mail infrastructure providers needed to deliver the service and, on request, to competent authorities, in line with KVKK Articles 8 and 9.',
    ),
    (
      'Collection method',
      'Data is collected electronically through the app, provided by you and generated automatically while you use it.',
    ),
    (
      'Your rights (KVKK Art. 11)',
      'You may ask whether your data is processed, request information about it, learn its purpose and the third parties it was transferred to, request correction, deletion or destruction, object to processing and claim compensation for damages. Send requests to $_e.',
    ),
  ],
};

final Map<String, List<LegalSection>> termsOfUse = {
  'tr': [
    (
      'Hizmet',
      'AIT, yüklediğin egzersiz videolarını yapay zekâ ile analiz ederek form puanı ve geri bildirim sunar. Hizmeti kullanarak bu koşulları kabul etmiş olursun.',
    ),
    (
      'Sağlık uyarısı',
      'Analizler bilgilendirme amaçlıdır; tıbbi tavsiye, teşhis veya fizyoterapist/antrenör değerlendirmesinin yerini tutmaz. Bir sağlık sorunun varsa egzersize başlamadan önce bir uzmana danış ve ağrı hissedersen egzersizi bırak.',
    ),
    (
      'Hesabın',
      'Hesap bilgilerinin doğru olmasından ve şifreni gizli tutmaktan sen sorumlusun. Hesabını dilediğin zaman uygulamadan silebilirsin.',
    ),
    (
      'Kabul edilebilir kullanım',
      'Yalnızca kendine ait ya da paylaşma iznin olan videoları yükle. Başkalarını rızaları olmadan kaydetmek, hizmeti aksatmaya çalışmak veya otomatik araçlarla aşırı istek göndermek yasaktır.',
    ),
    (
      'Sorumluluğun sınırı',
      'Hizmet "olduğu gibi" sunulur. Analiz sonuçlarının her zaman doğru olacağı garanti edilmez; sonuçlara dayanarak yapılan antrenmanlardan doğan zararlardan, yasaların izin verdiği ölçüde, sorumluluk kabul edilmez.',
    ),
    ('İletişim', 'Sorularını $_e adresine iletebilirsin.'),
  ],
  'en': [
    (
      'The service',
      'AIT analyzes the exercise videos you upload with AI and provides a form score and feedback. By using the service you accept these terms.',
    ),
    (
      'Health notice',
      'Analyses are for information only and don\'t replace medical advice, diagnosis or an assessment by a physiotherapist or coach. If you have a health condition, consult a professional before exercising, and stop if you feel pain.',
    ),
    (
      'Your account',
      'You are responsible for keeping your account details accurate and your password secret. You can delete your account in the app at any time.',
    ),
    (
      'Acceptable use',
      'Only upload videos of yourself or that you have permission to share. Recording others without consent, attempting to disrupt the service or sending excessive automated requests is prohibited.',
    ),
    (
      'Limitation of liability',
      'The service is provided "as is". Analysis results are not guaranteed to be accurate; to the extent permitted by law, no liability is accepted for harm arising from training based on them.',
    ),
    ('Contact', 'Send questions to $_e.'),
  ],
};
