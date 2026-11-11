// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Turkish (`tr`).
class AppLocalizationsTr extends AppLocalizations {
  AppLocalizationsTr([String locale = 'tr']) : super(locale);

  @override
  String get appName => 'AIT';

  @override
  String get appTagline => 'Formunu ölç. Daha iyi kaldır.';

  @override
  String get commonCancel => 'Vazgeç';

  @override
  String get commonClose => 'Kapat';

  @override
  String get commonContinue => 'Devam et';

  @override
  String get commonSave => 'Kaydet';

  @override
  String get commonDelete => 'Sil';

  @override
  String get commonRetry => 'Tekrar dene';

  @override
  String get commonOk => 'Tamam';

  @override
  String get commonSeeAll => 'Tümünü gör';

  @override
  String get commonComingSoon => 'Yakında';

  @override
  String get commonBack => 'Geri';

  @override
  String get commonDone => 'Bitti';

  @override
  String get commonEdit => 'Düzenle';

  @override
  String get commonAdd => 'Ekle';

  @override
  String get commonNotSet => 'Belirtilmedi';

  @override
  String get errorNetwork =>
      'Sunucuya ulaşılamadı. İnternet bağlantını kontrol et.';

  @override
  String get errorTimeout =>
      'Sunucu zamanında yanıt vermedi. Lütfen tekrar dene.';

  @override
  String get errorSessionExpired =>
      'Oturumun sona erdi. Lütfen tekrar giriş yap.';

  @override
  String get errorInvalidCredentials => 'E-posta veya şifre hatalı.';

  @override
  String get errorEmailTaken =>
      'Bu e-posta adresiyle kayıtlı bir hesap zaten var.';

  @override
  String get errorInvalidInput =>
      'Girilen bilgiler geçersiz. Lütfen kontrol et.';

  @override
  String get errorInvalidCode => 'Kod geçersiz veya süresi dolmuş.';

  @override
  String get errorTooLarge => 'Video dosyası çok büyük.';

  @override
  String get errorUnsupportedMedia =>
      'Dosya geçerli bir video değil. MP4, MOV veya AVI yükle.';

  @override
  String get errorRateLimited =>
      'Çok fazla istek gönderildi. Lütfen biraz sonra tekrar dene.';

  @override
  String get errorNotConfigured => 'Bu özellik henüz yapılandırılmadı.';

  @override
  String get errorUnavailable =>
      'Hizmet şu anda kullanılamıyor. Lütfen daha sonra tekrar dene.';

  @override
  String get errorAnalysisFailed =>
      'Video analiz edilemedi. Tüm vücudunun göründüğü net bir video dene.';

  @override
  String get analysisErrorNoPerson =>
      'Videoda vücudun net görünmedi. Telefonu sabitle, tüm vücudun kadrajda olsun ve iyi ışıkta tekrar çek.';

  @override
  String get analysisErrorUnreadable =>
      'Video açılamadı ya da eksik. Dosya bozuk olabilir; telefonunun kamerasıyla yeniden çekip tekrar yükle.';

  @override
  String get analysisErrorTooShort =>
      'Video çok kısa. En az 2 saniyelik ve en az bir tam tekrar içeren bir video yükle.';

  @override
  String get analysisErrorBodyOutOfFrame =>
      'Vücudunun bir kısmı (çoğunlukla ayaklar veya dizler) kadraj dışında kaldı. Telefonu biraz uzaklaştır, baştan ayağa görünecek şekilde çek.';

  @override
  String get analysisErrorUnsupported => 'Bu hareket henüz analiz edilemiyor.';

  @override
  String get analysisErrorUnsuitable =>
      'Video okunamadı veya analiz için uygun değil. Net ve kısa bir video yükle.';

  @override
  String get analysisErrorUnavailable =>
      'Analiz servisi şu an hazır değil. Biraz sonra tekrar dene.';

  @override
  String get analysisErrorInterrupted =>
      'Analiz yarıda kaldı çünkü sunucu yeniden başlatıldı. Videoyu tekrar yükle.';

  @override
  String get warningTitle => 'Kayıt hakkında';

  @override
  String get warningCameraTooFar =>
      'Kamera çok uzaktaydı; bir dahaki sefere biraz yaklaş.';

  @override
  String get warningCameraTooClose =>
      'Kamera çok yakındı; bir dahaki sefere biraz uzaklaş.';

  @override
  String get warningLowPoseConfidence =>
      'Vücudun bazı anlarda net algılanamadı; tüm vücudunun kadrajda olduğundan emin ol.';

  @override
  String get warningBodyPartlyOut =>
      'Vücudun bazı karelerde tam görünmedi; sonuçları buna göre değerlendir.';

  @override
  String get warningLowFrameRate =>
      'Videonun kare hızı düşük; sonuçlar daha az güvenilir olabilir.';

  @override
  String get errorServer => 'Sunucuda bir hata oluştu. Lütfen tekrar dene.';

  @override
  String get errorUnknown => 'Bir şeyler ters gitti. Lütfen tekrar dene.';

  @override
  String get exerciseSquat => 'Squat';

  @override
  String get exercisePushUp => 'Şınav';

  @override
  String get exercisePlank => 'Plank';

  @override
  String get exerciseLunge => 'Lunge';

  @override
  String get exerciseDeadlift => 'Deadlift';

  @override
  String get exerciseShoulderPress => 'Omuz press';

  @override
  String get exerciseSquatDescription =>
      'Alt vücut kuvvetini geliştiren temel bir bileşik hareket. Kalça, diz ve ayak bileği kontrolü doğru form için belirleyicidir.';

  @override
  String get exercisePushUpDescription =>
      'Göğüs, omuz ve kol kuvvetini geliştirirken gövde stabilitesini çalıştıran fonksiyonel bir hareket.';

  @override
  String get exercisePlankDescription =>
      'Core dayanıklılığını ve duruş stabilitesini geliştiren izometrik bir egzersiz.';

  @override
  String get exerciseLungeDescription =>
      'Tek bacak kuvveti, denge ve koordinasyon geliştiren bir alt vücut hareketi.';

  @override
  String get exerciseDeadliftDescription =>
      'Arka zincir kaslarını güçlendiren, kalçadan menteşe hareketine dayanan temel bir kuvvet egzersizi.';

  @override
  String get exerciseShoulderPressDescription =>
      'Omuz ve kol kuvvetini geliştiren, gövde kontrolü gerektiren bir itiş hareketi.';

  @override
  String get muscleCore => 'Core kasları';

  @override
  String get muscleCalves => 'Baldır kasları';

  @override
  String get squatMistake1 => 'Dizlerin içe çökmesi';

  @override
  String get squatMistake2 => 'Gövdenin fazla öne eğilmesi';

  @override
  String get squatMistake3 => 'Topukların yerden kalkması';

  @override
  String get squatMistake4 => 'Yetersiz derinlik';

  @override
  String get squatTip1 => 'Ayaklarını omuz genişliğinde aç.';

  @override
  String get squatTip2 => 'Dizlerini ayak parmaklarınla aynı hizada tut.';

  @override
  String get squatTip3 => 'İnerken ve kalkarken tempoyu kontrollü tut.';

  @override
  String get pushUpMistake1 => 'Kalçanın aşağı düşmesi';

  @override
  String get pushUpMistake2 => 'Dirseklerin fazla dışa açılması';

  @override
  String get pushUpMistake3 => 'Boynun öne uzatılması';

  @override
  String get pushUpMistake4 => 'Hareketin yarım bırakılması';

  @override
  String get pushUpTip1 => 'Omuz, kalça ve ayaklarını tek çizgide tut.';

  @override
  String get pushUpTip2 => 'Dirseklerini gövdene yaklaşık 45° açıyla bük.';

  @override
  String get pushUpTip3 =>
      'Göğsünü yere yakın indir, kolların tam açılana kadar it.';

  @override
  String get plankMistake1 => 'Belin aşağı çökmesi';

  @override
  String get plankMistake2 => 'Kalçanın fazla yukarı kalkması';

  @override
  String get plankMistake3 => 'Boynun nötr tutulmaması';

  @override
  String get plankTip1 => 'Dirseklerini omuzlarının altında tut.';

  @override
  String get plankTip2 => 'Karın ve kalça kaslarını sık.';

  @override
  String get plankTip3 => 'Nefesini tutma, düzenli nefes al.';

  @override
  String get lungeMistake1 => 'Ön dizin ayak ucunu çok geçmesi';

  @override
  String get lungeMistake2 => 'Gövdenin öne düşmesi';

  @override
  String get lungeMistake3 => 'Dengenin kaybedilmesi';

  @override
  String get lungeTip1 => 'Adımını yeterince uzun at.';

  @override
  String get lungeTip2 => 'Gövdeni dik tut.';

  @override
  String get lungeTip3 => 'Arka dizini yere yakın indir.';

  @override
  String get deadliftMistake1 => 'Sırtın yuvarlanması';

  @override
  String get deadliftMistake2 => 'Barın vücuttan uzaklaşması';

  @override
  String get deadliftMistake3 => 'Hareketi bel ile başlatmak';

  @override
  String get deadliftTip1 => 'Hareketi kalçadan menteşe yaparak başlat.';

  @override
  String get deadliftTip2 => 'Barı bacaklarına yakın tut.';

  @override
  String get deadliftTip3 => 'Sırtını nötr ve sabit tut.';

  @override
  String get shoulderPressMistake1 => 'Belin aşırı çukurlaşması';

  @override
  String get shoulderPressMistake2 => 'Dirseklerin fazla dışa açılması';

  @override
  String get shoulderPressMistake3 => 'Hareketin yarım yapılması';

  @override
  String get shoulderPressTip1 => 'Karın kaslarını sıkarak gövdeni sabitle.';

  @override
  String get shoulderPressTip2 => 'Ağırlığı başının üzerine düz bir hatta it.';

  @override
  String get shoulderPressTip3 => 'İnişi kontrollü yap.';

  @override
  String get issueInsufficientDepth => 'Yeterince derine inmedin.';

  @override
  String get issueInsufficientDepthFix =>
      'Kalçanı dizlerinle aynı seviyeye kadar indirmeyi hedefle.';

  @override
  String get issueKneeAngle => 'Diz açın yeterli seviyeye ulaşmadı.';

  @override
  String get issueKneeAngleFix =>
      'Kalçanı geriye iterek dizlerini daha fazla bük.';

  @override
  String get issueTooDeep =>
      'Çok derine indin ya da alt noktada dengesizleştin.';

  @override
  String get issueTooDeepFix =>
      'Alt noktada kontrolü kaybetmeden durabileceğin derinlikte kal.';

  @override
  String get issueTooFast => 'Hareketi çok hızlı yaptın.';

  @override
  String get issueTooFastFix =>
      'İnişi yaklaşık 2 saniyede, kalkışı kontrollü yap.';

  @override
  String get issueIncompleteRep => 'Bazı tekrarları tamamlamadın.';

  @override
  String get issueIncompleteRepFix => 'Her tekrarda tam inip tam kalk.';

  @override
  String get issueTorsoLean => 'Gövden fazla öne eğildi.';

  @override
  String get issueTorsoLeanFix => 'Göğsünü açık tut ve bakışını ileriye ver.';

  @override
  String get issueHipHinge => 'İnerken kalçadan yeterince bükülmedin.';

  @override
  String get issueHipHingeFix => 'İnişe kalçanı geriye iterek başla.';

  @override
  String get issueHipsSagging => 'Kalçan aşağı düştü.';

  @override
  String get issueHipsSaggingFix =>
      'Karın ve kalça kaslarını sıkarak vücudunu düz tut.';

  @override
  String get issueHipsTooHigh => 'Kalçan fazla yukarıda kaldı.';

  @override
  String get issueHipsTooHighFix =>
      'Kalçanı omuz ve topukların hizasına indir.';

  @override
  String get issueBackBent => 'Sırtın bükülmüş görünüyor.';

  @override
  String get issueBackBentFix =>
      'Başından topuklarına kadar düz bir çizgi oluştur.';

  @override
  String get issueNotLowEnough => 'Göğsün yeterince yere yaklaşmadı.';

  @override
  String get issueNotLowEnoughFix =>
      'Dirseklerin yaklaşık 90° bükülene kadar in.';

  @override
  String get issueIncompleteUp => 'Kolların tam açılmadı.';

  @override
  String get issueIncompleteUpFix =>
      'Her tekrarın sonunda kollarını tamamen aç.';

  @override
  String get issueElbowsFlared => 'Dirseklerin fazla dışa açıldı.';

  @override
  String get issueElbowsFlaredFix =>
      'Dirseklerini gövdene yaklaşık 45° açıyla tut.';

  @override
  String get issueShoulders => 'Omuz hizan bozuldu.';

  @override
  String get issueShouldersFix =>
      'Ellerini omuzlarının hemen altına yerleştir.';

  @override
  String get issueGeneric => 'Formunda düzeltilmesi gereken bir nokta var.';

  @override
  String get issueGenericFix => 'Hareketi yavaş ve kontrollü tekrarla.';

  @override
  String get issueNoReps => 'Tamamlanmış tekrar bulunamadı.';

  @override
  String get issueNoRepsFix =>
      'Hareketi en az bir kez baştan sona tamamla ve kameranın tüm vücudunu gördüğünden emin ol.';

  @override
  String get issueNoneTitle => 'Belirgin bir form hatası bulunmadı.';

  @override
  String get issueNoneMessage =>
      'Aynı kontrolü koruyarak tekrar sayını kademeli artırabilirsin.';

  @override
  String programSetsReps(int sets, int reps) {
    return '$sets set × $reps tekrar';
  }

  @override
  String programSetsSeconds(int sets, int seconds) {
    return '$sets set × $seconds sn';
  }

  @override
  String get focusLowerBody => 'Alt vücut';

  @override
  String get focusUpperBody => 'Üst vücut';

  @override
  String get focusRecovery => 'Toparlanma';

  @override
  String get focusFullBody => 'Tüm vücut';

  @override
  String get focusPosterior => 'Arka zincir';

  @override
  String get focusCoreMobility => 'Core ve mobilite';

  @override
  String get focusRest => 'Dinlenme';

  @override
  String get noteKneesOverToes => 'Diz ve ayak hizasını koru.';

  @override
  String get noteTorsoUpright => 'Gövdeni dik tut.';

  @override
  String get noteCoreBraced => 'Core bölgeni aktif tut.';

  @override
  String get noteHipsShouldersLine => 'Kalça ve omuz hizasını koru.';

  @override
  String get noteNoLowerBackArch => 'Belini fazla çukurlaştırma.';

  @override
  String get noteControlledDescent => 'İnişi kontrollü yap.';

  @override
  String get noteCoreStability => 'Gövde stabilitesini koru.';

  @override
  String get noteNoSag => 'Belinin çökmesine izin verme.';

  @override
  String get noteNeutralBack => 'Sırtını nötr tut.';

  @override
  String get noteBalance => 'Dengene odaklan.';

  @override
  String get noteBreathing => 'Nefesini düzenli tut.';

  @override
  String get noteMobility => 'Hareket açıklığına odaklan.';

  @override
  String get onboardingSkip => 'Atla';

  @override
  String get onboardingStart => 'Başla';

  @override
  String get onboardingCaptureTitle => 'Egzersizini kaydet';

  @override
  String get onboardingCaptureBody =>
      'Kamerayla kaydet ya da galeriden bir video seç. Tüm vücudunun göründüğü kısa bir video yeterli.';

  @override
  String get onboardingAnalyzeTitle => 'Formunu değerlendir';

  @override
  String get onboardingAnalyzeBody =>
      'Yapay zekâ tekrarlarını sayar, form puanını hesaplar ve düzeltmen gereken noktaları gösterir.';

  @override
  String get onboardingProgressTitle => 'Gelişimini takip et';

  @override
  String get onboardingProgressBody =>
      'Analizlerin hesabına kaydedilir. Puanının, kilonun ve ölçülerinin zaman içindeki değişimini gör.';

  @override
  String get commonPleaseWait => 'Lütfen bekle…';

  @override
  String get validationNameRequired => 'Ad soyad gerekli.';

  @override
  String get validationNameFull => 'Lütfen adını ve soyadını gir.';

  @override
  String get validationEmailRequired => 'E-posta adresi gerekli.';

  @override
  String get validationEmailInvalid =>
      'Geçerli bir e-posta adresi gir (ör. ad@ornek.com).';

  @override
  String get validationPasswordRequired => 'Şifre gerekli.';

  @override
  String validationPasswordMin(int min) {
    return 'Şifre en az $min karakter olmalı.';
  }

  @override
  String validationPasswordMax(int max) {
    return 'Şifre en fazla $max karakter olabilir.';
  }

  @override
  String get validationPasswordLetterDigit =>
      'Şifre en az bir harf ve bir rakam içermeli.';

  @override
  String get validationConfirmRequired => 'Şifreni tekrar gir.';

  @override
  String get validationPasswordsMismatch => 'Şifreler eşleşmiyor.';

  @override
  String get validationCode => '6 haneli kodu gir.';

  @override
  String get authShowPassword => 'Şifreyi göster';

  @override
  String get authHidePassword => 'Şifreyi gizle';

  @override
  String get authGoogleContinue => 'Google ile devam et';

  @override
  String get authGoogleSignUp => 'Google ile kayıt ol';

  @override
  String get authAppleContinue => 'Apple ile devam et';

  @override
  String get authAppleSignUp => 'Apple ile kayıt ol';

  @override
  String get authOr => 'veya';

  @override
  String authWelcomeBack(String name) {
    return 'Tekrar hoş geldin, $name!';
  }

  @override
  String authAccountCreated(String name) {
    return 'Hesabın oluşturuldu. Hoş geldin, $name!';
  }

  @override
  String get authEmail => 'E-posta adresi';

  @override
  String get authEmailHint => 'ad@ornek.com';

  @override
  String get authPassword => 'Şifre';

  @override
  String get authConfirmPassword => 'Şifre tekrarı';

  @override
  String get authFullName => 'Ad soyad';

  @override
  String get authFullNameHint => 'Ayşe Yılmaz';

  @override
  String get authRememberMe => 'Beni hatırla';

  @override
  String get authForgotPassword => 'Şifremi unuttum';

  @override
  String get authSignIn => 'Giriş yap';

  @override
  String get authSigningIn => 'Giriş yapılıyor…';

  @override
  String get authSignUp => 'Kayıt ol';

  @override
  String get authCreateAccount => 'Hesap oluştur';

  @override
  String get authCreatingAccount => 'Hesap oluşturuluyor…';

  @override
  String get authNoAccount => 'Hesabın yok mu?';

  @override
  String get authHaveAccount => 'Zaten hesabın var mı?';

  @override
  String get authTermsPrefix => '';

  @override
  String get authTermsMiddle => '\'nı ve ';

  @override
  String get authTermsSuffix => '\'nı okudum, kabul ediyorum.';

  @override
  String get authTermsRequired => 'Devam etmek için koşulları kabul etmelisin.';

  @override
  String authSocialNotConfigured(String provider) {
    return '$provider ile giriş bu cihazda henüz kullanılamıyor. Şimdilik e-posta ve şifre ile devam edebilirsin.';
  }

  @override
  String get authLoginTitle => 'Tekrar hoş geldin';

  @override
  String get authLoginSubtitle =>
      'Antrenmanlarına kaldığın yerden devam etmek için giriş yap.';

  @override
  String get authRegisterTitle => 'Hesabını oluştur';

  @override
  String get authRegisterSubtitle =>
      'Analizlerin hesabına kaydedilir; ilerlemeni her cihazdan takip edebilirsin.';

  @override
  String get authHeroTitle => 'Her tekrarda\ndaha doğru form.';

  @override
  String get authHeroBody =>
      'Videonu yükle; tekrarlarını sayalım, formunu ölçelim.';

  @override
  String get authFeatureCaptureTitle => 'Kaydet veya yükle';

  @override
  String get authFeatureCaptureBody =>
      'Kamerayla kaydet ya da galeriden video seç.';

  @override
  String get authFeatureFeedbackTitle => 'Net geri bildirim';

  @override
  String get authFeatureFeedbackBody =>
      'Form puanı, tekrar sayısı ve düzeltme önerileri.';

  @override
  String get authFeatureProgressTitle => 'Gelişim takibi';

  @override
  String get authFeatureProgressBody =>
      'Puanının ve ölçülerinin zaman içindeki değişimi.';

  @override
  String passwordRuleLength(int min) {
    return 'En az $min karakter';
  }

  @override
  String get passwordRuleLetter => 'Bir harf';

  @override
  String get passwordRuleDigit => 'Bir rakam';

  @override
  String get passwordRuleMet => 'karşılandı';

  @override
  String get passwordRuleUnmet => 'karşılanmadı';

  @override
  String get resetTitle => 'Şifre sıfırlama';

  @override
  String get resetIntro =>
      'Hesabının e-posta adresini gir; sana 6 haneli bir doğrulama kodu gönderelim.';

  @override
  String resetCodeSentBody(String email) {
    return '$email adresiyle kayıtlı bir hesap varsa kod gönderildi. Kodu ve yeni şifreni gir.';
  }

  @override
  String get resetSendCode => 'Kod gönder';

  @override
  String get resetCode => 'Doğrulama kodu';

  @override
  String get resetNewPassword => 'Yeni şifre';

  @override
  String get resetSetPassword => 'Şifreyi değiştir';

  @override
  String get resetResend => 'Kodu tekrar gönder';

  @override
  String resetResendIn(int seconds) {
    return '$seconds sn sonra tekrar gönderebilirsin';
  }

  @override
  String get resetSuccess =>
      'Şifren değiştirildi. Yeni şifrenle giriş yapabilirsin.';

  @override
  String get verifyTitle => 'E-posta adresini doğrula';

  @override
  String verifyBody(String email) {
    return '$email adresine gönderdiğimiz 6 haneli kodu gir.';
  }

  @override
  String get verifyAction => 'Doğrula';

  @override
  String get verifyResend => 'Yeni kod gönder';

  @override
  String get verifyCodeSent => 'Yeni kod e-posta adresine gönderildi.';

  @override
  String get verifySuccess => 'E-posta adresin doğrulandı.';

  @override
  String get legalTermsTitle => 'Kullanım Koşulları';

  @override
  String get legalPrivacyTitle => 'Gizlilik Politikası';

  @override
  String get navHome => 'Ana sayfa';

  @override
  String get navProgram => 'Program';

  @override
  String get navProgress => 'Gelişim';

  @override
  String get navHistory => 'Geçmiş';

  @override
  String get navProfile => 'Profil';

  @override
  String unitSeconds(int seconds) {
    return '$seconds sn';
  }

  @override
  String recordTitle(String exercise) {
    return '$exercise kaydı';
  }

  @override
  String get recordSwitchCamera => 'Kamerayı değiştir';

  @override
  String get recordFramingHint =>
      'Telefonu sabitle, 2-3 metre geri çekil ve tüm vücudunun çerçeveye girdiğinden emin ol.';

  @override
  String get recordGetReady => 'Hazırlan…';

  @override
  String get recordRecordingHint =>
      'Hareketi kontrollü yap. Bitirdiğinde durdur; en fazla 60 saniye kaydedilir.';

  @override
  String get recordGo => 'Başla';

  @override
  String get recordStart => 'Kaydı başlat';

  @override
  String get recordStop => 'Kaydı durdur';

  @override
  String get recordCameraError =>
      'Kameraya erişilemedi. Kamera iznini kontrol edip tekrar dene ya da galeriden video yükle.';

  @override
  String get progressTitle => 'Analiz';

  @override
  String get progressUploading => 'Video yükleniyor';

  @override
  String get progressQueued => 'Analiz sırasında';

  @override
  String get progressProcessing => 'Hareketin analiz ediliyor';

  @override
  String progressVideoSize(String size) {
    return '$size MB video';
  }

  @override
  String get progressLeaveHint =>
      'Bu ekrandan ayrılabilirsin; analiz bitince sonucu Geçmiş\'te görürsün.';

  @override
  String get progressFailedTitle => 'Analiz tamamlanamadı';

  @override
  String voiceResultSummary(int score, int reps, String issue) {
    return 'Analiz tamamlandı. Puanın $score. $reps tekrar. $issue';
  }

  @override
  String get scoreExcellent => 'Mükemmel';

  @override
  String get scoreGood => 'İyi';

  @override
  String get scoreFair => 'Geliştirilebilir';

  @override
  String get scoreNeedsWork => 'Çalışılmalı';

  @override
  String get resultScoreCaption => 'form puanı';

  @override
  String get resultNotScored => 'Puanlanamadı';

  @override
  String get resultNotScoredBody =>
      'Videoda tamamlanmış bir tekrar bulunamadı, bu yüzden puan verilmedi. Hareketi en az bir kez baştan sona tamamlayıp tekrar dene.';

  @override
  String get resultReps => 'Tekrar';

  @override
  String get resultDuration => 'Süre';

  @override
  String get resultConfidence => 'Algılama';

  @override
  String resultValidRepsNote(int valid, int total) {
    return '$total tekrarın $valid tanesi doğru formda tamamlandı.';
  }

  @override
  String get resultSummaryClean =>
      'Belirgin bir form hatası bulunmadı. Harika iş!';

  @override
  String resultSummaryIssues(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'Düzeltmen gereken $count nokta var.',
      one: 'Düzeltmen gereken 1 nokta var.',
    );
    return '$_temp0';
  }

  @override
  String get resultDepthTitle => 'Derinlik';

  @override
  String get resultAvgKneeAngle => 'Ortalama en düşük diz açısı';

  @override
  String get resultAvgKneeAngleHelp =>
      'Düşük değer daha derin squat demektir; 90° civarı yaygın bir hedeftir.';

  @override
  String get resultRangeOfMotion => 'Hareket açıklığı';

  @override
  String get resultRangeOfMotionHelp =>
      'Dizinin en açık ve en kapalı hali arasındaki fark.';

  @override
  String get resultIssuesTitle => 'Düzeltilecekler';

  @override
  String get resultTipsTitle => 'İpuçları';

  @override
  String get resultNewAnalysis => 'Yeni analiz';

  @override
  String get resultDisclaimer =>
      'Bu değerlendirme yapay zekâ tarafından üretilir ve tıbbi tavsiye değildir. Ağrı hissedersen egzersizi bırak.';

  @override
  String get homeTitle => 'Ana sayfa';

  @override
  String homeGreeting(String name) {
    return 'Merhaba, $name';
  }

  @override
  String get homeVerifyEmail =>
      'E-posta adresini doğrula; şifreni unutursan hesabına bu adresle erişeceksin.';

  @override
  String get homeNewAnalysis => 'Yeni analiz';

  @override
  String get homeNewAnalysisBody =>
      'Hareketi seç, sonra videonu yükle ya da kamerayla kaydet.';

  @override
  String get homeUploadVideo => 'Video yükle';

  @override
  String get homeRecordVideo => 'Kamerayla kaydet';

  @override
  String get homeCaptureTip =>
      'En iyi sonuç için tüm vücudun görünsün ve ortam aydınlık olsun.';

  @override
  String get homeSummary => 'Özet';

  @override
  String get homeThisWeek => 'Bu hafta';

  @override
  String get homeAverageScore => 'Ortalama';

  @override
  String get homeBestScore => 'En iyi';

  @override
  String get homeLatest => 'Son analiz';

  @override
  String get homeEmptyTitle => 'Henüz analiz yok';

  @override
  String get homeEmptyBody =>
      'İlk videonu analiz ettiğinde sonuçların burada görünecek.';

  @override
  String get homeToday => 'Bugünün programı';

  @override
  String get homeLibrary => 'Egzersizler';

  @override
  String get homeAiAnalysis => 'Form analizi';

  @override
  String get historyTitle => 'Geçmiş';

  @override
  String historyCount(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count analiz',
      one: '1 analiz',
    );
    return '$_temp0';
  }

  @override
  String historyReps(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: '$count tekrar',
      one: '1 tekrar',
    );
    return '$_temp0';
  }

  @override
  String get historyAll => 'Tümü';

  @override
  String get historyErrorTitle => 'Geçmiş yüklenemedi';

  @override
  String get historyNoMatch => 'Bu harekete ait analiz yok';

  @override
  String get historyNoMatchBody => 'Başka bir filtre seç.';

  @override
  String get detailFavorite => 'Favorilere ekle';

  @override
  String get detailUnfavorite => 'Favorilerden çıkar';

  @override
  String get detailComingSoonBody =>
      'Bu hareketin analizi henüz hazır değil. Şimdilik squat ve şınav analiz edilebiliyor.';

  @override
  String get detailMuscles => 'Çalışan kaslar';

  @override
  String get detailMistakes => 'Sık yapılan hatalar';

  @override
  String get progressPageTitle => 'Gelişim';

  @override
  String get progressPageSubtitle =>
      'Form puanını, kilonu ve ölçülerini takip et.';

  @override
  String get progressLocalNote =>
      'Kilo ve ölçü bilgileri yalnızca bu cihazda saklanır.';

  @override
  String get progressScoreTitle => 'Form puanı';

  @override
  String get progressScoreEmptyTitle => 'Trend için en az 2 analiz gerekli';

  @override
  String get progressScoreEmptyBody =>
      'Birkaç analiz yaptıkça form puanının nasıl değiştiğini burada göreceksin.';

  @override
  String get progressWeightTitle => 'Kilo';

  @override
  String get progressGoalAndHeight => 'Hedef ve boy';

  @override
  String get progressWeightEmptyTitle => 'Kilonu kaydet';

  @override
  String get progressWeightEmptyBody =>
      'Düzenli tartılıp kaydettikçe değişimini grafikte görebilirsin.';

  @override
  String get progressAddWeight => 'Kilo ekle';

  @override
  String progressGoal(String target) {
    return 'Hedef: $target kg';
  }

  @override
  String get progressHeight => 'Boy';

  @override
  String get progressTargetWeight => 'Hedef kilo';

  @override
  String progressRangeError(String min, String max, String unit) {
    return '$min ile $max $unit arasında bir değer gir.';
  }

  @override
  String get progressMeasurementsTitle => 'Vücut ölçüleri';

  @override
  String get progressMeasurementsEmptyTitle => 'Ölçü eklenmedi';

  @override
  String get progressMeasurementsEmptyBody =>
      'Bel, kalça gibi ölçülerini ekleyerek değişimi takip edebilirsin.';

  @override
  String get progressAddMeasurement => 'Ölçü ekle';

  @override
  String progressMeasurementFrom(String value) {
    return 'Başlangıç: $value cm';
  }

  @override
  String get measureWaist => 'Bel';

  @override
  String get measureHip => 'Kalça';

  @override
  String get measureChest => 'Göğüs';

  @override
  String get measureArm => 'Kol';

  @override
  String get measureThigh => 'Bacak';

  @override
  String get bmiTitle => 'Vücut kitle indeksi';

  @override
  String get bmiUnder => 'Zayıf';

  @override
  String get bmiNormal => 'Normal';

  @override
  String get bmiOver => 'Fazla kilolu';

  @override
  String get bmiObese => 'Obez';

  @override
  String get bmiNote => 'VKİ kas kütlesini dikkate almaz.';

  @override
  String get programTitle => 'Program';

  @override
  String get programSubtitle =>
      'Haftalık başlangıç programın. Tamamladığın günleri işaretle.';

  @override
  String get programThisWeek => 'Bu hafta';

  @override
  String programDaysDone(int done, int total) {
    return '$done/$total gün';
  }

  @override
  String get programToday => 'Bugün';

  @override
  String get programMarkDone => 'Günü tamamlandı olarak işaretle';

  @override
  String get programAnalyze => 'Kaydet ve analiz et';

  @override
  String get programRestDayBody =>
      'Dinlenme günü. Hafif yürüyüş veya esneme yapabilirsin.';

  @override
  String get profileTitle => 'Profil';

  @override
  String get profileAnalyses => 'Analiz';

  @override
  String get profileAchievements => 'Başarılar';

  @override
  String get profileFavorites => 'Favori egzersizler';

  @override
  String get profileVerified => 'Doğrulandı';

  @override
  String get profileNotVerified => 'Doğrulanmadı';

  @override
  String get achievementUnlocked => 'kazanıldı';

  @override
  String get achievementLocked => 'kilitli';

  @override
  String get achievementFirstTitle => 'İlk adım';

  @override
  String get achievementFirstBody => 'İlk analizini tamamla.';

  @override
  String get achievementTenTitle => 'Kararlı';

  @override
  String achievementTenBody(int count) {
    return '10 analiz tamamla ($count/10).';
  }

  @override
  String get achievementNinetyTitle => 'Kusursuza yakın';

  @override
  String get achievementNinetyBody => 'Bir analizde 90 veya üzeri puan al.';

  @override
  String get achievementCleanTitle => 'Temiz form';

  @override
  String get achievementCleanBody => 'Hiç form hatası olmadan bir set tamamla.';

  @override
  String get achievementBothTitle => 'Çok yönlü';

  @override
  String get achievementBothBody => 'Hem squat hem şınav analiz et.';

  @override
  String get achievementStreakTitle => 'Haftalık seri';

  @override
  String achievementStreakBody(int count) {
    return 'Bir hafta içinde 3 farklı gün analiz yap ($count/3).';
  }

  @override
  String get settingsTitle => 'Ayarlar';

  @override
  String get settingsAppearance => 'Görünüm';

  @override
  String get settingsThemeSystem => 'Sistem';

  @override
  String get settingsThemeLight => 'Açık';

  @override
  String get settingsThemeDark => 'Koyu';

  @override
  String get settingsLanguage => 'Dil';

  @override
  String get settingsVoice => 'Ses';

  @override
  String get settingsVoiceTitle => 'Sesli yönlendirme';

  @override
  String get settingsVoiceBody =>
      'Kayıt geri sayımını ve analiz sonucunu sesli okur.';

  @override
  String get settingsAccount => 'Hesap';

  @override
  String get settingsSignOut => 'Çıkış yap';

  @override
  String get settingsSignOutBody => 'Bu cihazda oturumun kapatılacak.';

  @override
  String get settingsSignOutAll => 'Tüm cihazlardan çıkış yap';

  @override
  String get settingsSignOutAllBody =>
      'Hesabının açık olduğu tüm cihazlarda oturum kapatılacak.';

  @override
  String get settingsDeleteTitle => 'Hesabımı sil';

  @override
  String get settingsDeleteBody =>
      'Hesabın, yüklediğin tüm videolar ve analiz sonuçların kalıcı olarak silinecek. Bu işlem geri alınamaz.';

  @override
  String get settingsDeleteAction => 'Kalıcı olarak sil';

  @override
  String get settingsDeleted => 'Hesabın ve tüm verilerin silindi.';

  @override
  String get settingsLegal => 'Yasal';

  @override
  String settingsVersion(String version) {
    return 'AIT sürüm $version';
  }

  @override
  String get legalKvkkTitle => 'KVKK Aydınlatma Metni';

  @override
  String legalLastUpdated(String date) {
    return 'Son güncelleme: $date';
  }

  @override
  String homeGreetingMorning(String name) {
    return 'Günaydın, $name';
  }

  @override
  String homeGreetingEvening(String name) {
    return 'İyi akşamlar, $name';
  }

  @override
  String homeSubtitle(String date) {
    return '$date · Bugün formunu bir adım ileri taşıyalım.';
  }

  @override
  String homeHeroStreak(int count) {
    String _temp0 = intl.Intl.pluralLogic(
      count,
      locale: localeName,
      other: 'Bu hafta $count analiz yaptın, harika gidiyorsun!',
      one: 'Bu hafta 1 analiz yaptın, harika gidiyorsun!',
    );
    return '$_temp0';
  }

  @override
  String get menuTitle => 'Menü';

  @override
  String get menuOpen => 'Menüyü aç';

  @override
  String get menuSubtitle => 'Bugün ne yapmak istersin?';

  @override
  String get menuProgressBody => 'Kilo, ölçüler ve VKİ';

  @override
  String get menuHistoryBody => 'Tüm analizlerin';

  @override
  String get menuSettingsBody => 'Tema, dil ve hesap';

  @override
  String get progressMyDetails => 'Bilgilerim';

  @override
  String get detailsTitle => 'Kişisel bilgilerin';

  @override
  String get detailsBody =>
      'Bu bilgiler sana özel hesaplamalar için kullanılır ve yalnızca bu cihazda saklanır.';

  @override
  String get sexLabel => 'Cinsiyet';

  @override
  String get sexFemale => 'Kadın';

  @override
  String get sexMale => 'Erkek';

  @override
  String get birthYearLabel => 'Doğum yılı';

  @override
  String get bmiPersonalizeTitle => 'Sana özel değerlendirme';

  @override
  String get bmiPersonalizeBody =>
      'Cinsiyetini ve doğum yılını eklersen vücut yağ oranını cinsiyetine göre hesaplayalım.';

  @override
  String get bmiNeedHeight => 'VKİ\'ni hesaplamak için boyunu ekle.';

  @override
  String get bmiBodyFat => 'Tahmini vücut yağı';

  @override
  String bmiBodyFatFor(String sex) {
    return '$sex için';
  }

  @override
  String bmiHealthyRange(String min, String max) {
    return 'Boyuna göre sağlıklı kilo: $min–$max kg';
  }

  @override
  String get bmiMethodNote =>
      'VKİ kadın ve erkekte aynı formülle hesaplanır. Vücut yağı ise cinsiyet ve yaşa göre tahmin edilir (Deurenberg formülü); ölçüm değildir.';

  @override
  String get bmiAdultsOnly =>
      'Vücut yağı tahmini 18 yaş ve üzeri için geçerlidir.';

  @override
  String get bodyFatEssential => 'Temel yağ';

  @override
  String get bodyFatAthletic => 'Atletik';

  @override
  String get bodyFatFitness => 'Fit';

  @override
  String get bodyFatAverage => 'Ortalama';

  @override
  String get bodyFatHigh => 'Yüksek';

  @override
  String get detailsSaved => 'Bilgilerin kaydedildi.';
}
