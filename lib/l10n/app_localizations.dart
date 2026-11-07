import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_tr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('tr'),
  ];

  /// No description provided for @appName.
  ///
  /// In tr, this message translates to:
  /// **'AIT'**
  String get appName;

  /// No description provided for @appTagline.
  ///
  /// In tr, this message translates to:
  /// **'Yapay zekâ destekli form analizi'**
  String get appTagline;

  /// No description provided for @commonCancel.
  ///
  /// In tr, this message translates to:
  /// **'Vazgeç'**
  String get commonCancel;

  /// No description provided for @commonClose.
  ///
  /// In tr, this message translates to:
  /// **'Kapat'**
  String get commonClose;

  /// No description provided for @commonContinue.
  ///
  /// In tr, this message translates to:
  /// **'Devam et'**
  String get commonContinue;

  /// No description provided for @commonSave.
  ///
  /// In tr, this message translates to:
  /// **'Kaydet'**
  String get commonSave;

  /// No description provided for @commonDelete.
  ///
  /// In tr, this message translates to:
  /// **'Sil'**
  String get commonDelete;

  /// No description provided for @commonRetry.
  ///
  /// In tr, this message translates to:
  /// **'Tekrar dene'**
  String get commonRetry;

  /// No description provided for @commonOk.
  ///
  /// In tr, this message translates to:
  /// **'Tamam'**
  String get commonOk;

  /// No description provided for @commonSeeAll.
  ///
  /// In tr, this message translates to:
  /// **'Tümünü gör'**
  String get commonSeeAll;

  /// No description provided for @commonComingSoon.
  ///
  /// In tr, this message translates to:
  /// **'Yakında'**
  String get commonComingSoon;

  /// No description provided for @commonBack.
  ///
  /// In tr, this message translates to:
  /// **'Geri'**
  String get commonBack;

  /// No description provided for @commonDone.
  ///
  /// In tr, this message translates to:
  /// **'Bitti'**
  String get commonDone;

  /// No description provided for @commonEdit.
  ///
  /// In tr, this message translates to:
  /// **'Düzenle'**
  String get commonEdit;

  /// No description provided for @commonAdd.
  ///
  /// In tr, this message translates to:
  /// **'Ekle'**
  String get commonAdd;

  /// No description provided for @commonNotSet.
  ///
  /// In tr, this message translates to:
  /// **'Belirtilmedi'**
  String get commonNotSet;

  /// No description provided for @errorNetwork.
  ///
  /// In tr, this message translates to:
  /// **'Sunucuya ulaşılamadı. İnternet bağlantını kontrol et.'**
  String get errorNetwork;

  /// No description provided for @errorTimeout.
  ///
  /// In tr, this message translates to:
  /// **'Sunucu zamanında yanıt vermedi. Lütfen tekrar dene.'**
  String get errorTimeout;

  /// No description provided for @errorSessionExpired.
  ///
  /// In tr, this message translates to:
  /// **'Oturumun sona erdi. Lütfen tekrar giriş yap.'**
  String get errorSessionExpired;

  /// No description provided for @errorInvalidCredentials.
  ///
  /// In tr, this message translates to:
  /// **'E-posta veya şifre hatalı.'**
  String get errorInvalidCredentials;

  /// No description provided for @errorEmailTaken.
  ///
  /// In tr, this message translates to:
  /// **'Bu e-posta adresiyle kayıtlı bir hesap zaten var.'**
  String get errorEmailTaken;

  /// No description provided for @errorInvalidInput.
  ///
  /// In tr, this message translates to:
  /// **'Girilen bilgiler geçersiz. Lütfen kontrol et.'**
  String get errorInvalidInput;

  /// No description provided for @errorInvalidCode.
  ///
  /// In tr, this message translates to:
  /// **'Kod geçersiz veya süresi dolmuş.'**
  String get errorInvalidCode;

  /// No description provided for @errorTooLarge.
  ///
  /// In tr, this message translates to:
  /// **'Video dosyası çok büyük.'**
  String get errorTooLarge;

  /// No description provided for @errorUnsupportedMedia.
  ///
  /// In tr, this message translates to:
  /// **'Dosya geçerli bir video değil. MP4, MOV veya AVI yükle.'**
  String get errorUnsupportedMedia;

  /// No description provided for @errorRateLimited.
  ///
  /// In tr, this message translates to:
  /// **'Çok fazla istek gönderildi. Lütfen biraz sonra tekrar dene.'**
  String get errorRateLimited;

  /// No description provided for @errorNotConfigured.
  ///
  /// In tr, this message translates to:
  /// **'Bu özellik henüz yapılandırılmadı.'**
  String get errorNotConfigured;

  /// No description provided for @errorUnavailable.
  ///
  /// In tr, this message translates to:
  /// **'Hizmet şu anda kullanılamıyor. Lütfen daha sonra tekrar dene.'**
  String get errorUnavailable;

  /// No description provided for @errorAnalysisFailed.
  ///
  /// In tr, this message translates to:
  /// **'Video analiz edilemedi. Tüm vücudunun göründüğü net bir video dene.'**
  String get errorAnalysisFailed;

  /// No description provided for @analysisErrorNoPerson.
  ///
  /// In tr, this message translates to:
  /// **'Videoda vücudun net görünmedi. Telefonu sabitle, tüm vücudun kadrajda olsun ve iyi ışıkta tekrar çek.'**
  String get analysisErrorNoPerson;

  /// No description provided for @analysisErrorUnreadable.
  ///
  /// In tr, this message translates to:
  /// **'Video açılamadı ya da eksik. Dosya bozuk olabilir; telefonunun kamerasıyla yeniden çekip tekrar yükle.'**
  String get analysisErrorUnreadable;

  /// No description provided for @analysisErrorTooShort.
  ///
  /// In tr, this message translates to:
  /// **'Video çok kısa. En az 2 saniyelik ve en az bir tam tekrar içeren bir video yükle.'**
  String get analysisErrorTooShort;

  /// No description provided for @analysisErrorBodyOutOfFrame.
  ///
  /// In tr, this message translates to:
  /// **'Vücudunun bir kısmı (çoğunlukla ayaklar veya dizler) kadraj dışında kaldı. Telefonu biraz uzaklaştır, baştan ayağa görünecek şekilde çek.'**
  String get analysisErrorBodyOutOfFrame;

  /// No description provided for @analysisErrorUnsupported.
  ///
  /// In tr, this message translates to:
  /// **'Bu hareket henüz analiz edilemiyor.'**
  String get analysisErrorUnsupported;

  /// No description provided for @analysisErrorUnsuitable.
  ///
  /// In tr, this message translates to:
  /// **'Video okunamadı veya analiz için uygun değil. Net ve kısa bir video yükle.'**
  String get analysisErrorUnsuitable;

  /// No description provided for @analysisErrorUnavailable.
  ///
  /// In tr, this message translates to:
  /// **'Analiz servisi şu an hazır değil. Biraz sonra tekrar dene.'**
  String get analysisErrorUnavailable;

  /// No description provided for @analysisErrorInterrupted.
  ///
  /// In tr, this message translates to:
  /// **'Analiz yarıda kaldı çünkü sunucu yeniden başlatıldı. Videoyu tekrar yükle.'**
  String get analysisErrorInterrupted;

  /// No description provided for @warningTitle.
  ///
  /// In tr, this message translates to:
  /// **'Kayıt hakkında'**
  String get warningTitle;

  /// No description provided for @warningCameraTooFar.
  ///
  /// In tr, this message translates to:
  /// **'Kamera çok uzaktaydı; bir dahaki sefere biraz yaklaş.'**
  String get warningCameraTooFar;

  /// No description provided for @warningCameraTooClose.
  ///
  /// In tr, this message translates to:
  /// **'Kamera çok yakındı; bir dahaki sefere biraz uzaklaş.'**
  String get warningCameraTooClose;

  /// No description provided for @warningLowPoseConfidence.
  ///
  /// In tr, this message translates to:
  /// **'Vücudun bazı anlarda net algılanamadı; tüm vücudunun kadrajda olduğundan emin ol.'**
  String get warningLowPoseConfidence;

  /// No description provided for @warningBodyPartlyOut.
  ///
  /// In tr, this message translates to:
  /// **'Vücudun bazı karelerde tam görünmedi; sonuçları buna göre değerlendir.'**
  String get warningBodyPartlyOut;

  /// No description provided for @warningLowFrameRate.
  ///
  /// In tr, this message translates to:
  /// **'Videonun kare hızı düşük; sonuçlar daha az güvenilir olabilir.'**
  String get warningLowFrameRate;

  /// No description provided for @errorServer.
  ///
  /// In tr, this message translates to:
  /// **'Sunucuda bir hata oluştu. Lütfen tekrar dene.'**
  String get errorServer;

  /// No description provided for @errorUnknown.
  ///
  /// In tr, this message translates to:
  /// **'Bir şeyler ters gitti. Lütfen tekrar dene.'**
  String get errorUnknown;

  /// No description provided for @exerciseSquat.
  ///
  /// In tr, this message translates to:
  /// **'Squat'**
  String get exerciseSquat;

  /// No description provided for @exercisePushUp.
  ///
  /// In tr, this message translates to:
  /// **'Şınav'**
  String get exercisePushUp;

  /// No description provided for @exercisePlank.
  ///
  /// In tr, this message translates to:
  /// **'Plank'**
  String get exercisePlank;

  /// No description provided for @exerciseLunge.
  ///
  /// In tr, this message translates to:
  /// **'Lunge'**
  String get exerciseLunge;

  /// No description provided for @exerciseDeadlift.
  ///
  /// In tr, this message translates to:
  /// **'Deadlift'**
  String get exerciseDeadlift;

  /// No description provided for @exerciseShoulderPress.
  ///
  /// In tr, this message translates to:
  /// **'Omuz press'**
  String get exerciseShoulderPress;

  /// No description provided for @exerciseSquatDescription.
  ///
  /// In tr, this message translates to:
  /// **'Alt vücut kuvvetini geliştiren temel bir bileşik hareket. Kalça, diz ve ayak bileği kontrolü doğru form için belirleyicidir.'**
  String get exerciseSquatDescription;

  /// No description provided for @exercisePushUpDescription.
  ///
  /// In tr, this message translates to:
  /// **'Göğüs, omuz ve kol kuvvetini geliştirirken gövde stabilitesini çalıştıran fonksiyonel bir hareket.'**
  String get exercisePushUpDescription;

  /// No description provided for @exercisePlankDescription.
  ///
  /// In tr, this message translates to:
  /// **'Core dayanıklılığını ve duruş stabilitesini geliştiren izometrik bir egzersiz.'**
  String get exercisePlankDescription;

  /// No description provided for @exerciseLungeDescription.
  ///
  /// In tr, this message translates to:
  /// **'Tek bacak kuvveti, denge ve koordinasyon geliştiren bir alt vücut hareketi.'**
  String get exerciseLungeDescription;

  /// No description provided for @exerciseDeadliftDescription.
  ///
  /// In tr, this message translates to:
  /// **'Arka zincir kaslarını güçlendiren, kalçadan menteşe hareketine dayanan temel bir kuvvet egzersizi.'**
  String get exerciseDeadliftDescription;

  /// No description provided for @exerciseShoulderPressDescription.
  ///
  /// In tr, this message translates to:
  /// **'Omuz ve kol kuvvetini geliştiren, gövde kontrolü gerektiren bir itiş hareketi.'**
  String get exerciseShoulderPressDescription;

  /// No description provided for @muscleCore.
  ///
  /// In tr, this message translates to:
  /// **'Core kasları'**
  String get muscleCore;

  /// No description provided for @muscleCalves.
  ///
  /// In tr, this message translates to:
  /// **'Baldır kasları'**
  String get muscleCalves;

  /// No description provided for @squatMistake1.
  ///
  /// In tr, this message translates to:
  /// **'Dizlerin içe çökmesi'**
  String get squatMistake1;

  /// No description provided for @squatMistake2.
  ///
  /// In tr, this message translates to:
  /// **'Gövdenin fazla öne eğilmesi'**
  String get squatMistake2;

  /// No description provided for @squatMistake3.
  ///
  /// In tr, this message translates to:
  /// **'Topukların yerden kalkması'**
  String get squatMistake3;

  /// No description provided for @squatMistake4.
  ///
  /// In tr, this message translates to:
  /// **'Yetersiz derinlik'**
  String get squatMistake4;

  /// No description provided for @squatTip1.
  ///
  /// In tr, this message translates to:
  /// **'Ayaklarını omuz genişliğinde aç.'**
  String get squatTip1;

  /// No description provided for @squatTip2.
  ///
  /// In tr, this message translates to:
  /// **'Dizlerini ayak parmaklarınla aynı hizada tut.'**
  String get squatTip2;

  /// No description provided for @squatTip3.
  ///
  /// In tr, this message translates to:
  /// **'İnerken ve kalkarken tempoyu kontrollü tut.'**
  String get squatTip3;

  /// No description provided for @pushUpMistake1.
  ///
  /// In tr, this message translates to:
  /// **'Kalçanın aşağı düşmesi'**
  String get pushUpMistake1;

  /// No description provided for @pushUpMistake2.
  ///
  /// In tr, this message translates to:
  /// **'Dirseklerin fazla dışa açılması'**
  String get pushUpMistake2;

  /// No description provided for @pushUpMistake3.
  ///
  /// In tr, this message translates to:
  /// **'Boynun öne uzatılması'**
  String get pushUpMistake3;

  /// No description provided for @pushUpMistake4.
  ///
  /// In tr, this message translates to:
  /// **'Hareketin yarım bırakılması'**
  String get pushUpMistake4;

  /// No description provided for @pushUpTip1.
  ///
  /// In tr, this message translates to:
  /// **'Omuz, kalça ve ayaklarını tek çizgide tut.'**
  String get pushUpTip1;

  /// No description provided for @pushUpTip2.
  ///
  /// In tr, this message translates to:
  /// **'Dirseklerini gövdene yaklaşık 45° açıyla bük.'**
  String get pushUpTip2;

  /// No description provided for @pushUpTip3.
  ///
  /// In tr, this message translates to:
  /// **'Göğsünü yere yakın indir, kolların tam açılana kadar it.'**
  String get pushUpTip3;

  /// No description provided for @plankMistake1.
  ///
  /// In tr, this message translates to:
  /// **'Belin aşağı çökmesi'**
  String get plankMistake1;

  /// No description provided for @plankMistake2.
  ///
  /// In tr, this message translates to:
  /// **'Kalçanın fazla yukarı kalkması'**
  String get plankMistake2;

  /// No description provided for @plankMistake3.
  ///
  /// In tr, this message translates to:
  /// **'Boynun nötr tutulmaması'**
  String get plankMistake3;

  /// No description provided for @plankTip1.
  ///
  /// In tr, this message translates to:
  /// **'Dirseklerini omuzlarının altında tut.'**
  String get plankTip1;

  /// No description provided for @plankTip2.
  ///
  /// In tr, this message translates to:
  /// **'Karın ve kalça kaslarını sık.'**
  String get plankTip2;

  /// No description provided for @plankTip3.
  ///
  /// In tr, this message translates to:
  /// **'Nefesini tutma, düzenli nefes al.'**
  String get plankTip3;

  /// No description provided for @lungeMistake1.
  ///
  /// In tr, this message translates to:
  /// **'Ön dizin ayak ucunu çok geçmesi'**
  String get lungeMistake1;

  /// No description provided for @lungeMistake2.
  ///
  /// In tr, this message translates to:
  /// **'Gövdenin öne düşmesi'**
  String get lungeMistake2;

  /// No description provided for @lungeMistake3.
  ///
  /// In tr, this message translates to:
  /// **'Dengenin kaybedilmesi'**
  String get lungeMistake3;

  /// No description provided for @lungeTip1.
  ///
  /// In tr, this message translates to:
  /// **'Adımını yeterince uzun at.'**
  String get lungeTip1;

  /// No description provided for @lungeTip2.
  ///
  /// In tr, this message translates to:
  /// **'Gövdeni dik tut.'**
  String get lungeTip2;

  /// No description provided for @lungeTip3.
  ///
  /// In tr, this message translates to:
  /// **'Arka dizini yere yakın indir.'**
  String get lungeTip3;

  /// No description provided for @deadliftMistake1.
  ///
  /// In tr, this message translates to:
  /// **'Sırtın yuvarlanması'**
  String get deadliftMistake1;

  /// No description provided for @deadliftMistake2.
  ///
  /// In tr, this message translates to:
  /// **'Barın vücuttan uzaklaşması'**
  String get deadliftMistake2;

  /// No description provided for @deadliftMistake3.
  ///
  /// In tr, this message translates to:
  /// **'Hareketi bel ile başlatmak'**
  String get deadliftMistake3;

  /// No description provided for @deadliftTip1.
  ///
  /// In tr, this message translates to:
  /// **'Hareketi kalçadan menteşe yaparak başlat.'**
  String get deadliftTip1;

  /// No description provided for @deadliftTip2.
  ///
  /// In tr, this message translates to:
  /// **'Barı bacaklarına yakın tut.'**
  String get deadliftTip2;

  /// No description provided for @deadliftTip3.
  ///
  /// In tr, this message translates to:
  /// **'Sırtını nötr ve sabit tut.'**
  String get deadliftTip3;

  /// No description provided for @shoulderPressMistake1.
  ///
  /// In tr, this message translates to:
  /// **'Belin aşırı çukurlaşması'**
  String get shoulderPressMistake1;

  /// No description provided for @shoulderPressMistake2.
  ///
  /// In tr, this message translates to:
  /// **'Dirseklerin fazla dışa açılması'**
  String get shoulderPressMistake2;

  /// No description provided for @shoulderPressMistake3.
  ///
  /// In tr, this message translates to:
  /// **'Hareketin yarım yapılması'**
  String get shoulderPressMistake3;

  /// No description provided for @shoulderPressTip1.
  ///
  /// In tr, this message translates to:
  /// **'Karın kaslarını sıkarak gövdeni sabitle.'**
  String get shoulderPressTip1;

  /// No description provided for @shoulderPressTip2.
  ///
  /// In tr, this message translates to:
  /// **'Ağırlığı başının üzerine düz bir hatta it.'**
  String get shoulderPressTip2;

  /// No description provided for @shoulderPressTip3.
  ///
  /// In tr, this message translates to:
  /// **'İnişi kontrollü yap.'**
  String get shoulderPressTip3;

  /// No description provided for @issueInsufficientDepth.
  ///
  /// In tr, this message translates to:
  /// **'Yeterince derine inmedin.'**
  String get issueInsufficientDepth;

  /// No description provided for @issueInsufficientDepthFix.
  ///
  /// In tr, this message translates to:
  /// **'Kalçanı dizlerinle aynı seviyeye kadar indirmeyi hedefle.'**
  String get issueInsufficientDepthFix;

  /// No description provided for @issueKneeAngle.
  ///
  /// In tr, this message translates to:
  /// **'Diz açın yeterli seviyeye ulaşmadı.'**
  String get issueKneeAngle;

  /// No description provided for @issueKneeAngleFix.
  ///
  /// In tr, this message translates to:
  /// **'Kalçanı geriye iterek dizlerini daha fazla bük.'**
  String get issueKneeAngleFix;

  /// No description provided for @issueTooDeep.
  ///
  /// In tr, this message translates to:
  /// **'Çok derine indin ya da alt noktada dengesizleştin.'**
  String get issueTooDeep;

  /// No description provided for @issueTooDeepFix.
  ///
  /// In tr, this message translates to:
  /// **'Alt noktada kontrolü kaybetmeden durabileceğin derinlikte kal.'**
  String get issueTooDeepFix;

  /// No description provided for @issueTooFast.
  ///
  /// In tr, this message translates to:
  /// **'Hareketi çok hızlı yaptın.'**
  String get issueTooFast;

  /// No description provided for @issueTooFastFix.
  ///
  /// In tr, this message translates to:
  /// **'İnişi yaklaşık 2 saniyede, kalkışı kontrollü yap.'**
  String get issueTooFastFix;

  /// No description provided for @issueIncompleteRep.
  ///
  /// In tr, this message translates to:
  /// **'Bazı tekrarları tamamlamadın.'**
  String get issueIncompleteRep;

  /// No description provided for @issueIncompleteRepFix.
  ///
  /// In tr, this message translates to:
  /// **'Her tekrarda tam inip tam kalk.'**
  String get issueIncompleteRepFix;

  /// No description provided for @issueTorsoLean.
  ///
  /// In tr, this message translates to:
  /// **'Gövden fazla öne eğildi.'**
  String get issueTorsoLean;

  /// No description provided for @issueTorsoLeanFix.
  ///
  /// In tr, this message translates to:
  /// **'Göğsünü açık tut ve bakışını ileriye ver.'**
  String get issueTorsoLeanFix;

  /// No description provided for @issueHipHinge.
  ///
  /// In tr, this message translates to:
  /// **'İnerken kalçadan yeterince bükülmedin.'**
  String get issueHipHinge;

  /// No description provided for @issueHipHingeFix.
  ///
  /// In tr, this message translates to:
  /// **'İnişe kalçanı geriye iterek başla.'**
  String get issueHipHingeFix;

  /// No description provided for @issueKneeValgus.
  ///
  /// In tr, this message translates to:
  /// **'Dizlerin içeri çöktü.'**
  String get issueKneeValgus;

  /// No description provided for @issueKneeValgusFix.
  ///
  /// In tr, this message translates to:
  /// **'Dizlerini ayak parmaklarınla aynı yöne, hafif dışarı it.'**
  String get issueKneeValgusFix;

  /// No description provided for @issueKneeShift.
  ///
  /// In tr, this message translates to:
  /// **'Dizlerin bir yana kaydı.'**
  String get issueKneeShift;

  /// No description provided for @issueKneeShiftFix.
  ///
  /// In tr, this message translates to:
  /// **'Ağırlığını iki ayağına eşit dağıt, dizlerini ortada tut.'**
  String get issueKneeShiftFix;

  /// No description provided for @issueHipsSagging.
  ///
  /// In tr, this message translates to:
  /// **'Kalçan aşağı düştü.'**
  String get issueHipsSagging;

  /// No description provided for @issueHipsSaggingFix.
  ///
  /// In tr, this message translates to:
  /// **'Karın ve kalça kaslarını sıkarak vücudunu düz tut.'**
  String get issueHipsSaggingFix;

  /// No description provided for @issueHipsTooHigh.
  ///
  /// In tr, this message translates to:
  /// **'Kalçan fazla yukarıda kaldı.'**
  String get issueHipsTooHigh;

  /// No description provided for @issueHipsTooHighFix.
  ///
  /// In tr, this message translates to:
  /// **'Kalçanı omuz ve topukların hizasına indir.'**
  String get issueHipsTooHighFix;

  /// No description provided for @issueBackBent.
  ///
  /// In tr, this message translates to:
  /// **'Sırtın bükülmüş görünüyor.'**
  String get issueBackBent;

  /// No description provided for @issueBackBentFix.
  ///
  /// In tr, this message translates to:
  /// **'Başından topuklarına kadar düz bir çizgi oluştur.'**
  String get issueBackBentFix;

  /// No description provided for @issueNotLowEnough.
  ///
  /// In tr, this message translates to:
  /// **'Göğsün yeterince yere yaklaşmadı.'**
  String get issueNotLowEnough;

  /// No description provided for @issueNotLowEnoughFix.
  ///
  /// In tr, this message translates to:
  /// **'Dirseklerin yaklaşık 90° bükülene kadar in.'**
  String get issueNotLowEnoughFix;

  /// No description provided for @issueIncompleteUp.
  ///
  /// In tr, this message translates to:
  /// **'Kolların tam açılmadı.'**
  String get issueIncompleteUp;

  /// No description provided for @issueIncompleteUpFix.
  ///
  /// In tr, this message translates to:
  /// **'Her tekrarın sonunda kollarını tamamen aç.'**
  String get issueIncompleteUpFix;

  /// No description provided for @issueElbowsFlared.
  ///
  /// In tr, this message translates to:
  /// **'Dirseklerin fazla dışa açıldı.'**
  String get issueElbowsFlared;

  /// No description provided for @issueElbowsFlaredFix.
  ///
  /// In tr, this message translates to:
  /// **'Dirseklerini gövdene yaklaşık 45° açıyla tut.'**
  String get issueElbowsFlaredFix;

  /// No description provided for @issueShoulders.
  ///
  /// In tr, this message translates to:
  /// **'Omuz hizan bozuldu.'**
  String get issueShoulders;

  /// No description provided for @issueShouldersFix.
  ///
  /// In tr, this message translates to:
  /// **'Ellerini omuzlarının hemen altına yerleştir.'**
  String get issueShouldersFix;

  /// No description provided for @issueGeneric.
  ///
  /// In tr, this message translates to:
  /// **'Formunda düzeltilmesi gereken bir nokta var.'**
  String get issueGeneric;

  /// No description provided for @issueGenericFix.
  ///
  /// In tr, this message translates to:
  /// **'Hareketi yavaş ve kontrollü tekrarla.'**
  String get issueGenericFix;

  /// No description provided for @issueNoReps.
  ///
  /// In tr, this message translates to:
  /// **'Tamamlanmış tekrar bulunamadı.'**
  String get issueNoReps;

  /// No description provided for @issueNoRepsFix.
  ///
  /// In tr, this message translates to:
  /// **'Hareketi en az bir kez baştan sona tamamla ve kameranın tüm vücudunu gördüğünden emin ol.'**
  String get issueNoRepsFix;

  /// No description provided for @issueNoneTitle.
  ///
  /// In tr, this message translates to:
  /// **'Belirgin bir form hatası bulunmadı.'**
  String get issueNoneTitle;

  /// No description provided for @issueNoneMessage.
  ///
  /// In tr, this message translates to:
  /// **'Aynı kontrolü koruyarak tekrar sayını kademeli artırabilirsin.'**
  String get issueNoneMessage;

  /// No description provided for @programSetsReps.
  ///
  /// In tr, this message translates to:
  /// **'{sets} set × {reps} tekrar'**
  String programSetsReps(int sets, int reps);

  /// No description provided for @programSetsSeconds.
  ///
  /// In tr, this message translates to:
  /// **'{sets} set × {seconds} sn'**
  String programSetsSeconds(int sets, int seconds);

  /// No description provided for @focusLowerBody.
  ///
  /// In tr, this message translates to:
  /// **'Alt vücut'**
  String get focusLowerBody;

  /// No description provided for @focusUpperBody.
  ///
  /// In tr, this message translates to:
  /// **'Üst vücut'**
  String get focusUpperBody;

  /// No description provided for @focusRecovery.
  ///
  /// In tr, this message translates to:
  /// **'Toparlanma'**
  String get focusRecovery;

  /// No description provided for @focusFullBody.
  ///
  /// In tr, this message translates to:
  /// **'Tüm vücut'**
  String get focusFullBody;

  /// No description provided for @focusPosterior.
  ///
  /// In tr, this message translates to:
  /// **'Arka zincir'**
  String get focusPosterior;

  /// No description provided for @focusCoreMobility.
  ///
  /// In tr, this message translates to:
  /// **'Core ve mobilite'**
  String get focusCoreMobility;

  /// No description provided for @focusRest.
  ///
  /// In tr, this message translates to:
  /// **'Dinlenme'**
  String get focusRest;

  /// No description provided for @noteKneesOverToes.
  ///
  /// In tr, this message translates to:
  /// **'Diz ve ayak hizasını koru.'**
  String get noteKneesOverToes;

  /// No description provided for @noteTorsoUpright.
  ///
  /// In tr, this message translates to:
  /// **'Gövdeni dik tut.'**
  String get noteTorsoUpright;

  /// No description provided for @noteCoreBraced.
  ///
  /// In tr, this message translates to:
  /// **'Core bölgeni aktif tut.'**
  String get noteCoreBraced;

  /// No description provided for @noteHipsShouldersLine.
  ///
  /// In tr, this message translates to:
  /// **'Kalça ve omuz hizasını koru.'**
  String get noteHipsShouldersLine;

  /// No description provided for @noteNoLowerBackArch.
  ///
  /// In tr, this message translates to:
  /// **'Belini fazla çukurlaştırma.'**
  String get noteNoLowerBackArch;

  /// No description provided for @noteControlledDescent.
  ///
  /// In tr, this message translates to:
  /// **'İnişi kontrollü yap.'**
  String get noteControlledDescent;

  /// No description provided for @noteCoreStability.
  ///
  /// In tr, this message translates to:
  /// **'Gövde stabilitesini koru.'**
  String get noteCoreStability;

  /// No description provided for @noteNoSag.
  ///
  /// In tr, this message translates to:
  /// **'Belinin çökmesine izin verme.'**
  String get noteNoSag;

  /// No description provided for @noteNeutralBack.
  ///
  /// In tr, this message translates to:
  /// **'Sırtını nötr tut.'**
  String get noteNeutralBack;

  /// No description provided for @noteBalance.
  ///
  /// In tr, this message translates to:
  /// **'Dengene odaklan.'**
  String get noteBalance;

  /// No description provided for @noteBreathing.
  ///
  /// In tr, this message translates to:
  /// **'Nefesini düzenli tut.'**
  String get noteBreathing;

  /// No description provided for @noteMobility.
  ///
  /// In tr, this message translates to:
  /// **'Hareket açıklığına odaklan.'**
  String get noteMobility;

  /// No description provided for @onboardingSkip.
  ///
  /// In tr, this message translates to:
  /// **'Atla'**
  String get onboardingSkip;

  /// No description provided for @onboardingStart.
  ///
  /// In tr, this message translates to:
  /// **'Başla'**
  String get onboardingStart;

  /// No description provided for @onboardingCaptureTitle.
  ///
  /// In tr, this message translates to:
  /// **'Egzersizini kaydet'**
  String get onboardingCaptureTitle;

  /// No description provided for @onboardingCaptureBody.
  ///
  /// In tr, this message translates to:
  /// **'Kamerayla kaydet ya da galeriden bir video seç. Tüm vücudunun göründüğü kısa bir video yeterli.'**
  String get onboardingCaptureBody;

  /// No description provided for @onboardingAnalyzeTitle.
  ///
  /// In tr, this message translates to:
  /// **'Formunu değerlendir'**
  String get onboardingAnalyzeTitle;

  /// No description provided for @onboardingAnalyzeBody.
  ///
  /// In tr, this message translates to:
  /// **'Yapay zekâ tekrarlarını sayar, form puanını hesaplar ve düzeltmen gereken noktaları gösterir.'**
  String get onboardingAnalyzeBody;

  /// No description provided for @onboardingProgressTitle.
  ///
  /// In tr, this message translates to:
  /// **'Gelişimini takip et'**
  String get onboardingProgressTitle;

  /// No description provided for @onboardingProgressBody.
  ///
  /// In tr, this message translates to:
  /// **'Analizlerin hesabına kaydedilir. Puanının, kilonun ve ölçülerinin zaman içindeki değişimini gör.'**
  String get onboardingProgressBody;

  /// No description provided for @commonPleaseWait.
  ///
  /// In tr, this message translates to:
  /// **'Lütfen bekle…'**
  String get commonPleaseWait;

  /// No description provided for @validationNameRequired.
  ///
  /// In tr, this message translates to:
  /// **'Ad soyad gerekli.'**
  String get validationNameRequired;

  /// No description provided for @validationNameFull.
  ///
  /// In tr, this message translates to:
  /// **'Lütfen adını ve soyadını gir.'**
  String get validationNameFull;

  /// No description provided for @validationEmailRequired.
  ///
  /// In tr, this message translates to:
  /// **'E-posta adresi gerekli.'**
  String get validationEmailRequired;

  /// No description provided for @validationEmailInvalid.
  ///
  /// In tr, this message translates to:
  /// **'Geçerli bir e-posta adresi gir (ör. ad@ornek.com).'**
  String get validationEmailInvalid;

  /// No description provided for @validationPasswordRequired.
  ///
  /// In tr, this message translates to:
  /// **'Şifre gerekli.'**
  String get validationPasswordRequired;

  /// No description provided for @validationPasswordMin.
  ///
  /// In tr, this message translates to:
  /// **'Şifre en az {min} karakter olmalı.'**
  String validationPasswordMin(int min);

  /// No description provided for @validationPasswordMax.
  ///
  /// In tr, this message translates to:
  /// **'Şifre en fazla {max} karakter olabilir.'**
  String validationPasswordMax(int max);

  /// No description provided for @validationPasswordLetterDigit.
  ///
  /// In tr, this message translates to:
  /// **'Şifre en az bir harf ve bir rakam içermeli.'**
  String get validationPasswordLetterDigit;

  /// No description provided for @validationConfirmRequired.
  ///
  /// In tr, this message translates to:
  /// **'Şifreni tekrar gir.'**
  String get validationConfirmRequired;

  /// No description provided for @validationPasswordsMismatch.
  ///
  /// In tr, this message translates to:
  /// **'Şifreler eşleşmiyor.'**
  String get validationPasswordsMismatch;

  /// No description provided for @validationCode.
  ///
  /// In tr, this message translates to:
  /// **'6 haneli kodu gir.'**
  String get validationCode;

  /// No description provided for @authShowPassword.
  ///
  /// In tr, this message translates to:
  /// **'Şifreyi göster'**
  String get authShowPassword;

  /// No description provided for @authHidePassword.
  ///
  /// In tr, this message translates to:
  /// **'Şifreyi gizle'**
  String get authHidePassword;

  /// No description provided for @authGoogleContinue.
  ///
  /// In tr, this message translates to:
  /// **'Google ile devam et'**
  String get authGoogleContinue;

  /// No description provided for @authGoogleSignUp.
  ///
  /// In tr, this message translates to:
  /// **'Google ile kayıt ol'**
  String get authGoogleSignUp;

  /// No description provided for @authAppleContinue.
  ///
  /// In tr, this message translates to:
  /// **'Apple ile devam et'**
  String get authAppleContinue;

  /// No description provided for @authAppleSignUp.
  ///
  /// In tr, this message translates to:
  /// **'Apple ile kayıt ol'**
  String get authAppleSignUp;

  /// No description provided for @authOr.
  ///
  /// In tr, this message translates to:
  /// **'veya'**
  String get authOr;

  /// No description provided for @authWelcomeBack.
  ///
  /// In tr, this message translates to:
  /// **'Tekrar hoş geldin, {name}!'**
  String authWelcomeBack(String name);

  /// No description provided for @authAccountCreated.
  ///
  /// In tr, this message translates to:
  /// **'Hesabın oluşturuldu. Hoş geldin, {name}!'**
  String authAccountCreated(String name);

  /// No description provided for @authEmail.
  ///
  /// In tr, this message translates to:
  /// **'E-posta adresi'**
  String get authEmail;

  /// No description provided for @authEmailHint.
  ///
  /// In tr, this message translates to:
  /// **'ad@ornek.com'**
  String get authEmailHint;

  /// No description provided for @authPassword.
  ///
  /// In tr, this message translates to:
  /// **'Şifre'**
  String get authPassword;

  /// No description provided for @authConfirmPassword.
  ///
  /// In tr, this message translates to:
  /// **'Şifre tekrarı'**
  String get authConfirmPassword;

  /// No description provided for @authFullName.
  ///
  /// In tr, this message translates to:
  /// **'Ad soyad'**
  String get authFullName;

  /// No description provided for @authFullNameHint.
  ///
  /// In tr, this message translates to:
  /// **'Ayşe Yılmaz'**
  String get authFullNameHint;

  /// No description provided for @authRememberMe.
  ///
  /// In tr, this message translates to:
  /// **'Beni hatırla'**
  String get authRememberMe;

  /// No description provided for @authForgotPassword.
  ///
  /// In tr, this message translates to:
  /// **'Şifremi unuttum'**
  String get authForgotPassword;

  /// No description provided for @authSignIn.
  ///
  /// In tr, this message translates to:
  /// **'Giriş yap'**
  String get authSignIn;

  /// No description provided for @authSigningIn.
  ///
  /// In tr, this message translates to:
  /// **'Giriş yapılıyor…'**
  String get authSigningIn;

  /// No description provided for @authSignUp.
  ///
  /// In tr, this message translates to:
  /// **'Kayıt ol'**
  String get authSignUp;

  /// No description provided for @authCreateAccount.
  ///
  /// In tr, this message translates to:
  /// **'Hesap oluştur'**
  String get authCreateAccount;

  /// No description provided for @authCreatingAccount.
  ///
  /// In tr, this message translates to:
  /// **'Hesap oluşturuluyor…'**
  String get authCreatingAccount;

  /// No description provided for @authNoAccount.
  ///
  /// In tr, this message translates to:
  /// **'Hesabın yok mu?'**
  String get authNoAccount;

  /// No description provided for @authHaveAccount.
  ///
  /// In tr, this message translates to:
  /// **'Zaten hesabın var mı?'**
  String get authHaveAccount;

  /// No description provided for @authTermsPrefix.
  ///
  /// In tr, this message translates to:
  /// **''**
  String get authTermsPrefix;

  /// No description provided for @authTermsMiddle.
  ///
  /// In tr, this message translates to:
  /// **'\'nı ve '**
  String get authTermsMiddle;

  /// No description provided for @authTermsSuffix.
  ///
  /// In tr, this message translates to:
  /// **'\'nı okudum, kabul ediyorum.'**
  String get authTermsSuffix;

  /// No description provided for @authTermsRequired.
  ///
  /// In tr, this message translates to:
  /// **'Devam etmek için koşulları kabul etmelisin.'**
  String get authTermsRequired;

  /// No description provided for @authSocialNotConfigured.
  ///
  /// In tr, this message translates to:
  /// **'{provider} ile giriş bu cihazda henüz kullanılamıyor. Şimdilik e-posta ve şifre ile devam edebilirsin.'**
  String authSocialNotConfigured(String provider);

  /// No description provided for @authLoginTitle.
  ///
  /// In tr, this message translates to:
  /// **'Tekrar hoş geldin'**
  String get authLoginTitle;

  /// No description provided for @authLoginSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Antrenmanlarına kaldığın yerden devam etmek için giriş yap.'**
  String get authLoginSubtitle;

  /// No description provided for @authRegisterTitle.
  ///
  /// In tr, this message translates to:
  /// **'Hesabını oluştur'**
  String get authRegisterTitle;

  /// No description provided for @authRegisterSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Analizlerin hesabına kaydedilir; ilerlemeni her cihazdan takip edebilirsin.'**
  String get authRegisterSubtitle;

  /// No description provided for @authHeroTitle.
  ///
  /// In tr, this message translates to:
  /// **'Her tekrarda\ndaha doğru form.'**
  String get authHeroTitle;

  /// No description provided for @authHeroBody.
  ///
  /// In tr, this message translates to:
  /// **'Videonu yükle, yapay zekâ tekrarlarını saysın ve formunu değerlendirsin.'**
  String get authHeroBody;

  /// No description provided for @authFeatureCaptureTitle.
  ///
  /// In tr, this message translates to:
  /// **'Kaydet veya yükle'**
  String get authFeatureCaptureTitle;

  /// No description provided for @authFeatureCaptureBody.
  ///
  /// In tr, this message translates to:
  /// **'Kamerayla kaydet ya da galeriden video seç.'**
  String get authFeatureCaptureBody;

  /// No description provided for @authFeatureFeedbackTitle.
  ///
  /// In tr, this message translates to:
  /// **'Net geri bildirim'**
  String get authFeatureFeedbackTitle;

  /// No description provided for @authFeatureFeedbackBody.
  ///
  /// In tr, this message translates to:
  /// **'Form puanı, tekrar sayısı ve düzeltme önerileri.'**
  String get authFeatureFeedbackBody;

  /// No description provided for @authFeatureProgressTitle.
  ///
  /// In tr, this message translates to:
  /// **'Gelişim takibi'**
  String get authFeatureProgressTitle;

  /// No description provided for @authFeatureProgressBody.
  ///
  /// In tr, this message translates to:
  /// **'Puanının ve ölçülerinin zaman içindeki değişimi.'**
  String get authFeatureProgressBody;

  /// No description provided for @passwordRuleLength.
  ///
  /// In tr, this message translates to:
  /// **'En az {min} karakter'**
  String passwordRuleLength(int min);

  /// No description provided for @passwordRuleLetter.
  ///
  /// In tr, this message translates to:
  /// **'Bir harf'**
  String get passwordRuleLetter;

  /// No description provided for @passwordRuleDigit.
  ///
  /// In tr, this message translates to:
  /// **'Bir rakam'**
  String get passwordRuleDigit;

  /// No description provided for @passwordRuleMet.
  ///
  /// In tr, this message translates to:
  /// **'karşılandı'**
  String get passwordRuleMet;

  /// No description provided for @passwordRuleUnmet.
  ///
  /// In tr, this message translates to:
  /// **'karşılanmadı'**
  String get passwordRuleUnmet;

  /// No description provided for @resetTitle.
  ///
  /// In tr, this message translates to:
  /// **'Şifre sıfırlama'**
  String get resetTitle;

  /// No description provided for @resetIntro.
  ///
  /// In tr, this message translates to:
  /// **'Hesabının e-posta adresini gir; sana 6 haneli bir doğrulama kodu gönderelim.'**
  String get resetIntro;

  /// No description provided for @resetCodeSentBody.
  ///
  /// In tr, this message translates to:
  /// **'{email} adresiyle kayıtlı bir hesap varsa kod gönderildi. Kodu ve yeni şifreni gir.'**
  String resetCodeSentBody(String email);

  /// No description provided for @resetSendCode.
  ///
  /// In tr, this message translates to:
  /// **'Kod gönder'**
  String get resetSendCode;

  /// No description provided for @resetCode.
  ///
  /// In tr, this message translates to:
  /// **'Doğrulama kodu'**
  String get resetCode;

  /// No description provided for @resetNewPassword.
  ///
  /// In tr, this message translates to:
  /// **'Yeni şifre'**
  String get resetNewPassword;

  /// No description provided for @resetSetPassword.
  ///
  /// In tr, this message translates to:
  /// **'Şifreyi değiştir'**
  String get resetSetPassword;

  /// No description provided for @resetResend.
  ///
  /// In tr, this message translates to:
  /// **'Kodu tekrar gönder'**
  String get resetResend;

  /// No description provided for @resetResendIn.
  ///
  /// In tr, this message translates to:
  /// **'{seconds} sn sonra tekrar gönderebilirsin'**
  String resetResendIn(int seconds);

  /// No description provided for @resetSuccess.
  ///
  /// In tr, this message translates to:
  /// **'Şifren değiştirildi. Yeni şifrenle giriş yapabilirsin.'**
  String get resetSuccess;

  /// No description provided for @verifyTitle.
  ///
  /// In tr, this message translates to:
  /// **'E-posta adresini doğrula'**
  String get verifyTitle;

  /// No description provided for @verifyBody.
  ///
  /// In tr, this message translates to:
  /// **'{email} adresine gönderdiğimiz 6 haneli kodu gir.'**
  String verifyBody(String email);

  /// No description provided for @verifyAction.
  ///
  /// In tr, this message translates to:
  /// **'Doğrula'**
  String get verifyAction;

  /// No description provided for @verifyResend.
  ///
  /// In tr, this message translates to:
  /// **'Yeni kod gönder'**
  String get verifyResend;

  /// No description provided for @verifyCodeSent.
  ///
  /// In tr, this message translates to:
  /// **'Yeni kod e-posta adresine gönderildi.'**
  String get verifyCodeSent;

  /// No description provided for @verifySuccess.
  ///
  /// In tr, this message translates to:
  /// **'E-posta adresin doğrulandı.'**
  String get verifySuccess;

  /// No description provided for @legalTermsTitle.
  ///
  /// In tr, this message translates to:
  /// **'Kullanım Koşulları'**
  String get legalTermsTitle;

  /// No description provided for @legalPrivacyTitle.
  ///
  /// In tr, this message translates to:
  /// **'Gizlilik Politikası'**
  String get legalPrivacyTitle;

  /// No description provided for @navHome.
  ///
  /// In tr, this message translates to:
  /// **'Ana sayfa'**
  String get navHome;

  /// No description provided for @navProgram.
  ///
  /// In tr, this message translates to:
  /// **'Program'**
  String get navProgram;

  /// No description provided for @navProgress.
  ///
  /// In tr, this message translates to:
  /// **'Gelişim'**
  String get navProgress;

  /// No description provided for @navHistory.
  ///
  /// In tr, this message translates to:
  /// **'Geçmiş'**
  String get navHistory;

  /// No description provided for @navProfile.
  ///
  /// In tr, this message translates to:
  /// **'Profil'**
  String get navProfile;

  /// No description provided for @unitSeconds.
  ///
  /// In tr, this message translates to:
  /// **'{seconds} sn'**
  String unitSeconds(int seconds);

  /// No description provided for @recordTitle.
  ///
  /// In tr, this message translates to:
  /// **'{exercise} kaydı'**
  String recordTitle(String exercise);

  /// No description provided for @recordSwitchCamera.
  ///
  /// In tr, this message translates to:
  /// **'Kamerayı değiştir'**
  String get recordSwitchCamera;

  /// No description provided for @recordFramingHint.
  ///
  /// In tr, this message translates to:
  /// **'Telefonu sabitle, 2-3 metre geri çekil ve tüm vücudunun çerçeveye girdiğinden emin ol.'**
  String get recordFramingHint;

  /// No description provided for @recordGetReady.
  ///
  /// In tr, this message translates to:
  /// **'Hazırlan…'**
  String get recordGetReady;

  /// No description provided for @recordRecordingHint.
  ///
  /// In tr, this message translates to:
  /// **'Hareketi kontrollü yap. Bitirdiğinde durdur; en fazla 60 saniye kaydedilir.'**
  String get recordRecordingHint;

  /// No description provided for @recordGo.
  ///
  /// In tr, this message translates to:
  /// **'Başla'**
  String get recordGo;

  /// No description provided for @recordStart.
  ///
  /// In tr, this message translates to:
  /// **'Kaydı başlat'**
  String get recordStart;

  /// No description provided for @recordStop.
  ///
  /// In tr, this message translates to:
  /// **'Kaydı durdur'**
  String get recordStop;

  /// No description provided for @recordCameraError.
  ///
  /// In tr, this message translates to:
  /// **'Kameraya erişilemedi. Kamera iznini kontrol edip tekrar dene ya da galeriden video yükle.'**
  String get recordCameraError;

  /// No description provided for @progressTitle.
  ///
  /// In tr, this message translates to:
  /// **'Analiz'**
  String get progressTitle;

  /// No description provided for @progressUploading.
  ///
  /// In tr, this message translates to:
  /// **'Video yükleniyor'**
  String get progressUploading;

  /// No description provided for @progressQueued.
  ///
  /// In tr, this message translates to:
  /// **'Analiz sırasında'**
  String get progressQueued;

  /// No description provided for @progressProcessing.
  ///
  /// In tr, this message translates to:
  /// **'Hareketin analiz ediliyor'**
  String get progressProcessing;

  /// No description provided for @progressVideoSize.
  ///
  /// In tr, this message translates to:
  /// **'{size} MB video'**
  String progressVideoSize(String size);

  /// No description provided for @progressLeaveHint.
  ///
  /// In tr, this message translates to:
  /// **'Bu ekrandan ayrılabilirsin; analiz bitince sonucu Geçmiş\'te görürsün.'**
  String get progressLeaveHint;

  /// No description provided for @progressFailedTitle.
  ///
  /// In tr, this message translates to:
  /// **'Analiz tamamlanamadı'**
  String get progressFailedTitle;

  /// No description provided for @voiceResultSummary.
  ///
  /// In tr, this message translates to:
  /// **'Analiz tamamlandı. Puanın {score}. {reps} tekrar. {issue}'**
  String voiceResultSummary(int score, int reps, String issue);

  /// No description provided for @scoreExcellent.
  ///
  /// In tr, this message translates to:
  /// **'Mükemmel'**
  String get scoreExcellent;

  /// No description provided for @scoreGood.
  ///
  /// In tr, this message translates to:
  /// **'İyi'**
  String get scoreGood;

  /// No description provided for @scoreFair.
  ///
  /// In tr, this message translates to:
  /// **'Geliştirilebilir'**
  String get scoreFair;

  /// No description provided for @scoreNeedsWork.
  ///
  /// In tr, this message translates to:
  /// **'Çalışılmalı'**
  String get scoreNeedsWork;

  /// No description provided for @resultScoreCaption.
  ///
  /// In tr, this message translates to:
  /// **'form puanı'**
  String get resultScoreCaption;

  /// No description provided for @resultNotScored.
  ///
  /// In tr, this message translates to:
  /// **'Puanlanamadı'**
  String get resultNotScored;

  /// No description provided for @resultNotScoredBody.
  ///
  /// In tr, this message translates to:
  /// **'Videoda tamamlanmış bir tekrar bulunamadı, bu yüzden puan verilmedi. Hareketi en az bir kez baştan sona tamamlayıp tekrar dene.'**
  String get resultNotScoredBody;

  /// No description provided for @resultReps.
  ///
  /// In tr, this message translates to:
  /// **'Tekrar'**
  String get resultReps;

  /// No description provided for @resultDuration.
  ///
  /// In tr, this message translates to:
  /// **'Süre'**
  String get resultDuration;

  /// No description provided for @resultConfidence.
  ///
  /// In tr, this message translates to:
  /// **'Algılama'**
  String get resultConfidence;

  /// No description provided for @resultValidRepsNote.
  ///
  /// In tr, this message translates to:
  /// **'{total} tekrarın {valid} tanesi doğru formda tamamlandı.'**
  String resultValidRepsNote(int valid, int total);

  /// No description provided for @resultSummaryClean.
  ///
  /// In tr, this message translates to:
  /// **'Belirgin bir form hatası bulunmadı. Harika iş!'**
  String get resultSummaryClean;

  /// No description provided for @resultSummaryIssues.
  ///
  /// In tr, this message translates to:
  /// **'{count, plural, =1{Düzeltmen gereken 1 nokta var.} other{Düzeltmen gereken {count} nokta var.}}'**
  String resultSummaryIssues(int count);

  /// No description provided for @resultDepthTitle.
  ///
  /// In tr, this message translates to:
  /// **'Derinlik'**
  String get resultDepthTitle;

  /// No description provided for @resultAvgKneeAngle.
  ///
  /// In tr, this message translates to:
  /// **'Ortalama en düşük diz açısı'**
  String get resultAvgKneeAngle;

  /// No description provided for @resultAvgKneeAngleHelp.
  ///
  /// In tr, this message translates to:
  /// **'Düşük değer daha derin squat demektir; 90° civarı yaygın bir hedeftir.'**
  String get resultAvgKneeAngleHelp;

  /// No description provided for @resultRangeOfMotion.
  ///
  /// In tr, this message translates to:
  /// **'Hareket açıklığı'**
  String get resultRangeOfMotion;

  /// No description provided for @resultRangeOfMotionHelp.
  ///
  /// In tr, this message translates to:
  /// **'Dizinin en açık ve en kapalı hali arasındaki fark.'**
  String get resultRangeOfMotionHelp;

  /// No description provided for @resultIssuesTitle.
  ///
  /// In tr, this message translates to:
  /// **'Düzeltilecekler'**
  String get resultIssuesTitle;

  /// No description provided for @resultTipsTitle.
  ///
  /// In tr, this message translates to:
  /// **'İpuçları'**
  String get resultTipsTitle;

  /// No description provided for @resultNewAnalysis.
  ///
  /// In tr, this message translates to:
  /// **'Yeni analiz'**
  String get resultNewAnalysis;

  /// No description provided for @resultDisclaimer.
  ///
  /// In tr, this message translates to:
  /// **'Bu değerlendirme yapay zekâ tarafından üretilir ve tıbbi tavsiye değildir. Ağrı hissedersen egzersizi bırak.'**
  String get resultDisclaimer;

  /// No description provided for @homeTitle.
  ///
  /// In tr, this message translates to:
  /// **'Ana sayfa'**
  String get homeTitle;

  /// No description provided for @homeGreeting.
  ///
  /// In tr, this message translates to:
  /// **'Merhaba, {name}'**
  String homeGreeting(String name);

  /// No description provided for @homeVerifyEmail.
  ///
  /// In tr, this message translates to:
  /// **'E-posta adresini doğrula; şifreni unutursan hesabına bu adresle erişeceksin.'**
  String get homeVerifyEmail;

  /// No description provided for @homeNewAnalysis.
  ///
  /// In tr, this message translates to:
  /// **'Yeni analiz'**
  String get homeNewAnalysis;

  /// No description provided for @homeNewAnalysisBody.
  ///
  /// In tr, this message translates to:
  /// **'Hareketi seç, sonra videonu yükle ya da kamerayla kaydet.'**
  String get homeNewAnalysisBody;

  /// No description provided for @homeUploadVideo.
  ///
  /// In tr, this message translates to:
  /// **'Video yükle'**
  String get homeUploadVideo;

  /// No description provided for @homeRecordVideo.
  ///
  /// In tr, this message translates to:
  /// **'Kamerayla kaydet'**
  String get homeRecordVideo;

  /// No description provided for @homeCaptureTip.
  ///
  /// In tr, this message translates to:
  /// **'En iyi sonuç için tüm vücudun görünsün ve ortam aydınlık olsun.'**
  String get homeCaptureTip;

  /// No description provided for @homeSummary.
  ///
  /// In tr, this message translates to:
  /// **'Özet'**
  String get homeSummary;

  /// No description provided for @homeThisWeek.
  ///
  /// In tr, this message translates to:
  /// **'Bu hafta'**
  String get homeThisWeek;

  /// No description provided for @homeAverageScore.
  ///
  /// In tr, this message translates to:
  /// **'Ortalama'**
  String get homeAverageScore;

  /// No description provided for @homeBestScore.
  ///
  /// In tr, this message translates to:
  /// **'En iyi'**
  String get homeBestScore;

  /// No description provided for @homeLatest.
  ///
  /// In tr, this message translates to:
  /// **'Son analiz'**
  String get homeLatest;

  /// No description provided for @homeEmptyTitle.
  ///
  /// In tr, this message translates to:
  /// **'Henüz analiz yok'**
  String get homeEmptyTitle;

  /// No description provided for @homeEmptyBody.
  ///
  /// In tr, this message translates to:
  /// **'İlk videonu analiz ettiğinde sonuçların burada görünecek.'**
  String get homeEmptyBody;

  /// No description provided for @homeToday.
  ///
  /// In tr, this message translates to:
  /// **'Bugünün programı'**
  String get homeToday;

  /// No description provided for @homeLibrary.
  ///
  /// In tr, this message translates to:
  /// **'Egzersizler'**
  String get homeLibrary;

  /// No description provided for @homeAiAnalysis.
  ///
  /// In tr, this message translates to:
  /// **'AI analizi'**
  String get homeAiAnalysis;

  /// No description provided for @historyTitle.
  ///
  /// In tr, this message translates to:
  /// **'Geçmiş'**
  String get historyTitle;

  /// No description provided for @historyCount.
  ///
  /// In tr, this message translates to:
  /// **'{count, plural, =1{1 analiz} other{{count} analiz}}'**
  String historyCount(int count);

  /// No description provided for @historyReps.
  ///
  /// In tr, this message translates to:
  /// **'{count, plural, =1{1 tekrar} other{{count} tekrar}}'**
  String historyReps(int count);

  /// No description provided for @historyAll.
  ///
  /// In tr, this message translates to:
  /// **'Tümü'**
  String get historyAll;

  /// No description provided for @historyErrorTitle.
  ///
  /// In tr, this message translates to:
  /// **'Geçmiş yüklenemedi'**
  String get historyErrorTitle;

  /// No description provided for @historyNoMatch.
  ///
  /// In tr, this message translates to:
  /// **'Bu harekete ait analiz yok'**
  String get historyNoMatch;

  /// No description provided for @historyNoMatchBody.
  ///
  /// In tr, this message translates to:
  /// **'Başka bir filtre seç.'**
  String get historyNoMatchBody;

  /// No description provided for @detailFavorite.
  ///
  /// In tr, this message translates to:
  /// **'Favorilere ekle'**
  String get detailFavorite;

  /// No description provided for @detailUnfavorite.
  ///
  /// In tr, this message translates to:
  /// **'Favorilerden çıkar'**
  String get detailUnfavorite;

  /// No description provided for @detailComingSoonBody.
  ///
  /// In tr, this message translates to:
  /// **'Bu hareket için yapay zekâ analizi henüz hazır değil. Şimdilik squat ve şınav analiz edilebiliyor.'**
  String get detailComingSoonBody;

  /// No description provided for @detailMuscles.
  ///
  /// In tr, this message translates to:
  /// **'Çalışan kaslar'**
  String get detailMuscles;

  /// No description provided for @detailMistakes.
  ///
  /// In tr, this message translates to:
  /// **'Sık yapılan hatalar'**
  String get detailMistakes;

  /// No description provided for @progressPageTitle.
  ///
  /// In tr, this message translates to:
  /// **'Gelişim'**
  String get progressPageTitle;

  /// No description provided for @progressPageSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Form puanını, kilonu ve ölçülerini takip et.'**
  String get progressPageSubtitle;

  /// No description provided for @progressLocalNote.
  ///
  /// In tr, this message translates to:
  /// **'Kilo ve ölçü bilgileri yalnızca bu cihazda saklanır.'**
  String get progressLocalNote;

  /// No description provided for @progressScoreTitle.
  ///
  /// In tr, this message translates to:
  /// **'Form puanı'**
  String get progressScoreTitle;

  /// No description provided for @progressScoreEmptyTitle.
  ///
  /// In tr, this message translates to:
  /// **'Trend için en az 2 analiz gerekli'**
  String get progressScoreEmptyTitle;

  /// No description provided for @progressScoreEmptyBody.
  ///
  /// In tr, this message translates to:
  /// **'Birkaç analiz yaptıkça form puanının nasıl değiştiğini burada göreceksin.'**
  String get progressScoreEmptyBody;

  /// No description provided for @progressWeightTitle.
  ///
  /// In tr, this message translates to:
  /// **'Kilo'**
  String get progressWeightTitle;

  /// No description provided for @progressGoalAndHeight.
  ///
  /// In tr, this message translates to:
  /// **'Hedef ve boy'**
  String get progressGoalAndHeight;

  /// No description provided for @progressWeightEmptyTitle.
  ///
  /// In tr, this message translates to:
  /// **'Kilonu kaydet'**
  String get progressWeightEmptyTitle;

  /// No description provided for @progressWeightEmptyBody.
  ///
  /// In tr, this message translates to:
  /// **'Düzenli tartılıp kaydettikçe değişimini grafikte görebilirsin.'**
  String get progressWeightEmptyBody;

  /// No description provided for @progressAddWeight.
  ///
  /// In tr, this message translates to:
  /// **'Kilo ekle'**
  String get progressAddWeight;

  /// No description provided for @progressGoal.
  ///
  /// In tr, this message translates to:
  /// **'Hedef: {target} kg'**
  String progressGoal(String target);

  /// No description provided for @progressHeight.
  ///
  /// In tr, this message translates to:
  /// **'Boy'**
  String get progressHeight;

  /// No description provided for @progressTargetWeight.
  ///
  /// In tr, this message translates to:
  /// **'Hedef kilo'**
  String get progressTargetWeight;

  /// No description provided for @progressRangeError.
  ///
  /// In tr, this message translates to:
  /// **'{min} ile {max} {unit} arasında bir değer gir.'**
  String progressRangeError(String min, String max, String unit);

  /// No description provided for @progressMeasurementsTitle.
  ///
  /// In tr, this message translates to:
  /// **'Vücut ölçüleri'**
  String get progressMeasurementsTitle;

  /// No description provided for @progressMeasurementsEmptyTitle.
  ///
  /// In tr, this message translates to:
  /// **'Ölçü eklenmedi'**
  String get progressMeasurementsEmptyTitle;

  /// No description provided for @progressMeasurementsEmptyBody.
  ///
  /// In tr, this message translates to:
  /// **'Bel, kalça gibi ölçülerini ekleyerek değişimi takip edebilirsin.'**
  String get progressMeasurementsEmptyBody;

  /// No description provided for @progressAddMeasurement.
  ///
  /// In tr, this message translates to:
  /// **'Ölçü ekle'**
  String get progressAddMeasurement;

  /// No description provided for @progressMeasurementFrom.
  ///
  /// In tr, this message translates to:
  /// **'Başlangıç: {value} cm'**
  String progressMeasurementFrom(String value);

  /// No description provided for @measureWaist.
  ///
  /// In tr, this message translates to:
  /// **'Bel'**
  String get measureWaist;

  /// No description provided for @measureHip.
  ///
  /// In tr, this message translates to:
  /// **'Kalça'**
  String get measureHip;

  /// No description provided for @measureChest.
  ///
  /// In tr, this message translates to:
  /// **'Göğüs'**
  String get measureChest;

  /// No description provided for @measureArm.
  ///
  /// In tr, this message translates to:
  /// **'Kol'**
  String get measureArm;

  /// No description provided for @measureThigh.
  ///
  /// In tr, this message translates to:
  /// **'Bacak'**
  String get measureThigh;

  /// No description provided for @bmiTitle.
  ///
  /// In tr, this message translates to:
  /// **'Vücut kitle indeksi'**
  String get bmiTitle;

  /// No description provided for @bmiUnder.
  ///
  /// In tr, this message translates to:
  /// **'Zayıf'**
  String get bmiUnder;

  /// No description provided for @bmiNormal.
  ///
  /// In tr, this message translates to:
  /// **'Normal'**
  String get bmiNormal;

  /// No description provided for @bmiOver.
  ///
  /// In tr, this message translates to:
  /// **'Fazla kilolu'**
  String get bmiOver;

  /// No description provided for @bmiObese.
  ///
  /// In tr, this message translates to:
  /// **'Obez'**
  String get bmiObese;

  /// No description provided for @bmiNote.
  ///
  /// In tr, this message translates to:
  /// **'VKİ kas kütlesini dikkate almaz.'**
  String get bmiNote;

  /// No description provided for @programTitle.
  ///
  /// In tr, this message translates to:
  /// **'Program'**
  String get programTitle;

  /// No description provided for @programSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Haftalık başlangıç programın. Tamamladığın günleri işaretle.'**
  String get programSubtitle;

  /// No description provided for @programThisWeek.
  ///
  /// In tr, this message translates to:
  /// **'Bu hafta'**
  String get programThisWeek;

  /// No description provided for @programDaysDone.
  ///
  /// In tr, this message translates to:
  /// **'{done}/{total} gün'**
  String programDaysDone(int done, int total);

  /// No description provided for @programToday.
  ///
  /// In tr, this message translates to:
  /// **'Bugün'**
  String get programToday;

  /// No description provided for @programMarkDone.
  ///
  /// In tr, this message translates to:
  /// **'Günü tamamlandı olarak işaretle'**
  String get programMarkDone;

  /// No description provided for @programAnalyze.
  ///
  /// In tr, this message translates to:
  /// **'Kaydet ve analiz et'**
  String get programAnalyze;

  /// No description provided for @programRestDayBody.
  ///
  /// In tr, this message translates to:
  /// **'Dinlenme günü. Hafif yürüyüş veya esneme yapabilirsin.'**
  String get programRestDayBody;

  /// No description provided for @profileTitle.
  ///
  /// In tr, this message translates to:
  /// **'Profil'**
  String get profileTitle;

  /// No description provided for @profileAnalyses.
  ///
  /// In tr, this message translates to:
  /// **'Analiz'**
  String get profileAnalyses;

  /// No description provided for @profileAchievements.
  ///
  /// In tr, this message translates to:
  /// **'Başarılar'**
  String get profileAchievements;

  /// No description provided for @profileFavorites.
  ///
  /// In tr, this message translates to:
  /// **'Favori egzersizler'**
  String get profileFavorites;

  /// No description provided for @profileVerified.
  ///
  /// In tr, this message translates to:
  /// **'Doğrulandı'**
  String get profileVerified;

  /// No description provided for @profileNotVerified.
  ///
  /// In tr, this message translates to:
  /// **'Doğrulanmadı'**
  String get profileNotVerified;

  /// No description provided for @achievementUnlocked.
  ///
  /// In tr, this message translates to:
  /// **'kazanıldı'**
  String get achievementUnlocked;

  /// No description provided for @achievementLocked.
  ///
  /// In tr, this message translates to:
  /// **'kilitli'**
  String get achievementLocked;

  /// No description provided for @achievementFirstTitle.
  ///
  /// In tr, this message translates to:
  /// **'İlk adım'**
  String get achievementFirstTitle;

  /// No description provided for @achievementFirstBody.
  ///
  /// In tr, this message translates to:
  /// **'İlk analizini tamamla.'**
  String get achievementFirstBody;

  /// No description provided for @achievementTenTitle.
  ///
  /// In tr, this message translates to:
  /// **'Kararlı'**
  String get achievementTenTitle;

  /// No description provided for @achievementTenBody.
  ///
  /// In tr, this message translates to:
  /// **'10 analiz tamamla ({count}/10).'**
  String achievementTenBody(int count);

  /// No description provided for @achievementNinetyTitle.
  ///
  /// In tr, this message translates to:
  /// **'Kusursuza yakın'**
  String get achievementNinetyTitle;

  /// No description provided for @achievementNinetyBody.
  ///
  /// In tr, this message translates to:
  /// **'Bir analizde 90 veya üzeri puan al.'**
  String get achievementNinetyBody;

  /// No description provided for @achievementCleanTitle.
  ///
  /// In tr, this message translates to:
  /// **'Temiz form'**
  String get achievementCleanTitle;

  /// No description provided for @achievementCleanBody.
  ///
  /// In tr, this message translates to:
  /// **'Hiç form hatası olmadan bir set tamamla.'**
  String get achievementCleanBody;

  /// No description provided for @achievementBothTitle.
  ///
  /// In tr, this message translates to:
  /// **'Çok yönlü'**
  String get achievementBothTitle;

  /// No description provided for @achievementBothBody.
  ///
  /// In tr, this message translates to:
  /// **'Hem squat hem şınav analiz et.'**
  String get achievementBothBody;

  /// No description provided for @achievementStreakTitle.
  ///
  /// In tr, this message translates to:
  /// **'Haftalık seri'**
  String get achievementStreakTitle;

  /// No description provided for @achievementStreakBody.
  ///
  /// In tr, this message translates to:
  /// **'Bir hafta içinde 3 farklı gün analiz yap ({count}/3).'**
  String achievementStreakBody(int count);

  /// No description provided for @settingsTitle.
  ///
  /// In tr, this message translates to:
  /// **'Ayarlar'**
  String get settingsTitle;

  /// No description provided for @settingsAppearance.
  ///
  /// In tr, this message translates to:
  /// **'Görünüm'**
  String get settingsAppearance;

  /// No description provided for @settingsThemeSystem.
  ///
  /// In tr, this message translates to:
  /// **'Sistem'**
  String get settingsThemeSystem;

  /// No description provided for @settingsThemeLight.
  ///
  /// In tr, this message translates to:
  /// **'Açık'**
  String get settingsThemeLight;

  /// No description provided for @settingsThemeDark.
  ///
  /// In tr, this message translates to:
  /// **'Koyu'**
  String get settingsThemeDark;

  /// No description provided for @settingsLanguage.
  ///
  /// In tr, this message translates to:
  /// **'Dil'**
  String get settingsLanguage;

  /// No description provided for @settingsVoice.
  ///
  /// In tr, this message translates to:
  /// **'Ses'**
  String get settingsVoice;

  /// No description provided for @settingsVoiceTitle.
  ///
  /// In tr, this message translates to:
  /// **'Sesli yönlendirme'**
  String get settingsVoiceTitle;

  /// No description provided for @settingsVoiceBody.
  ///
  /// In tr, this message translates to:
  /// **'Kayıt geri sayımını ve analiz sonucunu sesli okur.'**
  String get settingsVoiceBody;

  /// No description provided for @settingsAccount.
  ///
  /// In tr, this message translates to:
  /// **'Hesap'**
  String get settingsAccount;

  /// No description provided for @settingsSignOut.
  ///
  /// In tr, this message translates to:
  /// **'Çıkış yap'**
  String get settingsSignOut;

  /// No description provided for @settingsSignOutBody.
  ///
  /// In tr, this message translates to:
  /// **'Bu cihazda oturumun kapatılacak.'**
  String get settingsSignOutBody;

  /// No description provided for @settingsSignOutAll.
  ///
  /// In tr, this message translates to:
  /// **'Tüm cihazlardan çıkış yap'**
  String get settingsSignOutAll;

  /// No description provided for @settingsSignOutAllBody.
  ///
  /// In tr, this message translates to:
  /// **'Hesabının açık olduğu tüm cihazlarda oturum kapatılacak.'**
  String get settingsSignOutAllBody;

  /// No description provided for @settingsDeleteTitle.
  ///
  /// In tr, this message translates to:
  /// **'Hesabımı sil'**
  String get settingsDeleteTitle;

  /// No description provided for @settingsDeleteBody.
  ///
  /// In tr, this message translates to:
  /// **'Hesabın, yüklediğin tüm videolar ve analiz sonuçların kalıcı olarak silinecek. Bu işlem geri alınamaz.'**
  String get settingsDeleteBody;

  /// No description provided for @settingsDeleteAction.
  ///
  /// In tr, this message translates to:
  /// **'Kalıcı olarak sil'**
  String get settingsDeleteAction;

  /// No description provided for @settingsDeleted.
  ///
  /// In tr, this message translates to:
  /// **'Hesabın ve tüm verilerin silindi.'**
  String get settingsDeleted;

  /// No description provided for @settingsLegal.
  ///
  /// In tr, this message translates to:
  /// **'Yasal'**
  String get settingsLegal;

  /// No description provided for @settingsVersion.
  ///
  /// In tr, this message translates to:
  /// **'AIT sürüm {version}'**
  String settingsVersion(String version);

  /// No description provided for @legalKvkkTitle.
  ///
  /// In tr, this message translates to:
  /// **'KVKK Aydınlatma Metni'**
  String get legalKvkkTitle;

  /// No description provided for @legalLastUpdated.
  ///
  /// In tr, this message translates to:
  /// **'Son güncelleme: {date}'**
  String legalLastUpdated(String date);

  /// No description provided for @homeGreetingMorning.
  ///
  /// In tr, this message translates to:
  /// **'Günaydın, {name}'**
  String homeGreetingMorning(String name);

  /// No description provided for @homeGreetingEvening.
  ///
  /// In tr, this message translates to:
  /// **'İyi akşamlar, {name}'**
  String homeGreetingEvening(String name);

  /// No description provided for @homeSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'{date} · Bugün formunu bir adım ileri taşıyalım.'**
  String homeSubtitle(String date);

  /// No description provided for @homeHeroStreak.
  ///
  /// In tr, this message translates to:
  /// **'Bu hafta {count} analiz yaptın, harika gidiyorsun!'**
  String homeHeroStreak(int count);

  /// No description provided for @menuTitle.
  ///
  /// In tr, this message translates to:
  /// **'Menü'**
  String get menuTitle;

  /// No description provided for @menuOpen.
  ///
  /// In tr, this message translates to:
  /// **'Menüyü aç'**
  String get menuOpen;

  /// No description provided for @menuSubtitle.
  ///
  /// In tr, this message translates to:
  /// **'Bugün ne yapmak istersin?'**
  String get menuSubtitle;

  /// No description provided for @menuProgressBody.
  ///
  /// In tr, this message translates to:
  /// **'Kilo, ölçüler ve VKİ'**
  String get menuProgressBody;

  /// No description provided for @menuHistoryBody.
  ///
  /// In tr, this message translates to:
  /// **'Tüm analizlerin'**
  String get menuHistoryBody;

  /// No description provided for @menuSettingsBody.
  ///
  /// In tr, this message translates to:
  /// **'Tema, dil ve hesap'**
  String get menuSettingsBody;

  /// No description provided for @progressMyDetails.
  ///
  /// In tr, this message translates to:
  /// **'Bilgilerim'**
  String get progressMyDetails;

  /// No description provided for @detailsTitle.
  ///
  /// In tr, this message translates to:
  /// **'Kişisel bilgilerin'**
  String get detailsTitle;

  /// No description provided for @detailsBody.
  ///
  /// In tr, this message translates to:
  /// **'Bu bilgiler sana özel hesaplamalar için kullanılır ve yalnızca bu cihazda saklanır.'**
  String get detailsBody;

  /// No description provided for @sexLabel.
  ///
  /// In tr, this message translates to:
  /// **'Cinsiyet'**
  String get sexLabel;

  /// No description provided for @sexFemale.
  ///
  /// In tr, this message translates to:
  /// **'Kadın'**
  String get sexFemale;

  /// No description provided for @sexMale.
  ///
  /// In tr, this message translates to:
  /// **'Erkek'**
  String get sexMale;

  /// No description provided for @birthYearLabel.
  ///
  /// In tr, this message translates to:
  /// **'Doğum yılı'**
  String get birthYearLabel;

  /// No description provided for @bmiPersonalizeTitle.
  ///
  /// In tr, this message translates to:
  /// **'Sana özel değerlendirme'**
  String get bmiPersonalizeTitle;

  /// No description provided for @bmiPersonalizeBody.
  ///
  /// In tr, this message translates to:
  /// **'Cinsiyetini ve doğum yılını eklersen vücut yağ oranını cinsiyetine göre hesaplayalım.'**
  String get bmiPersonalizeBody;

  /// No description provided for @bmiNeedHeight.
  ///
  /// In tr, this message translates to:
  /// **'VKİ\'ni hesaplamak için boyunu ekle.'**
  String get bmiNeedHeight;

  /// No description provided for @bmiBodyFat.
  ///
  /// In tr, this message translates to:
  /// **'Tahmini vücut yağı'**
  String get bmiBodyFat;

  /// No description provided for @bmiBodyFatFor.
  ///
  /// In tr, this message translates to:
  /// **'{sex} için'**
  String bmiBodyFatFor(String sex);

  /// No description provided for @bmiHealthyRange.
  ///
  /// In tr, this message translates to:
  /// **'Boyuna göre sağlıklı kilo: {min}–{max} kg'**
  String bmiHealthyRange(String min, String max);

  /// No description provided for @bmiMethodNote.
  ///
  /// In tr, this message translates to:
  /// **'VKİ kadın ve erkekte aynı formülle hesaplanır. Vücut yağı ise cinsiyet ve yaşa göre tahmin edilir (Deurenberg formülü); ölçüm değildir.'**
  String get bmiMethodNote;

  /// No description provided for @bmiAdultsOnly.
  ///
  /// In tr, this message translates to:
  /// **'Vücut yağı tahmini 18 yaş ve üzeri için geçerlidir.'**
  String get bmiAdultsOnly;

  /// No description provided for @bodyFatEssential.
  ///
  /// In tr, this message translates to:
  /// **'Temel yağ'**
  String get bodyFatEssential;

  /// No description provided for @bodyFatAthletic.
  ///
  /// In tr, this message translates to:
  /// **'Atletik'**
  String get bodyFatAthletic;

  /// No description provided for @bodyFatFitness.
  ///
  /// In tr, this message translates to:
  /// **'Fit'**
  String get bodyFatFitness;

  /// No description provided for @bodyFatAverage.
  ///
  /// In tr, this message translates to:
  /// **'Ortalama'**
  String get bodyFatAverage;

  /// No description provided for @bodyFatHigh.
  ///
  /// In tr, this message translates to:
  /// **'Yüksek'**
  String get bodyFatHigh;

  /// No description provided for @detailsSaved.
  ///
  /// In tr, this message translates to:
  /// **'Bilgilerin kaydedildi.'**
  String get detailsSaved;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'tr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'tr':
      return AppLocalizationsTr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
