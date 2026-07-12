import '../models/exercise_detail_model.dart';

const List<ExerciseDetail> exerciseDetails = [
  ExerciseDetail(
    name: 'Squat',
    description:
        'Squat, alt ekstremite kuvvetini geliştiren temel bir bileşik egzersizdir. Kalça, diz ve ayak bileği kontrolü doğru form için kritiktir.',
    targetMuscles: [
      'Quadriceps',
      'Gluteus Maximus',
      'Hamstrings',
      'Core kasları',
    ],
    commonMistakes: [
      'Dizlerin içe doğru çökmesi',
      'Gövdenin fazla öne eğilmesi',
      'Topukların yerden kalkması',
      'Yetersiz kalça derinliği',
    ],
    tips: [
      'Ayakları omuz genişliğinde konumlandır.',
      'Dizleri ayak parmaklarıyla aynı hizada tut.',
      'Göğsü açık ve sırtı kontrollü tut.',
      'İniş ve kalkış fazını yavaş yap.',
    ],
  ),
  ExerciseDetail(
    name: 'Push-up',
    description:
        'Push-up, üst ekstremite ve core stabilizasyonunu geliştiren fonksiyonel bir egzersizdir. Omuz, dirsek ve gövde hizası önemlidir.',
    targetMuscles: [
      'Pectoralis Major',
      'Triceps Brachii',
      'Anterior Deltoid',
      'Core kasları',
    ],
    commonMistakes: [
      'Kalçanın aşağı düşmesi',
      'Dirseklerin fazla dışa açılması',
      'Boynun öne uzatılması',
      'Gövde hattının bozulması',
    ],
    tips: [
      'Omuz, kalça ve ayak hizasını düz tut.',
      'Core bölgesini aktif tut.',
      'Dirsekleri kontrollü şekilde bük.',
      'Hareketi tam açıklıkta ve kontrollü yap.',
    ],
  ),
  ExerciseDetail(
    name: 'Plank',
    description:
        'Plank, core dayanıklılığını ve postüral stabilizasyonu geliştiren izometrik bir egzersizdir.',
    targetMuscles: [
      'Rectus Abdominis',
      'Transversus Abdominis',
      'Obliques',
      'Gluteal kaslar',
    ],
    commonMistakes: [
      'Belin aşağı çökmesi',
      'Kalçanın fazla yukarı kalkması',
      'Omuz-dirsek hizasının bozulması',
      'Boynun nötr pozisyonda tutulmaması',
    ],
    tips: [
      'Dirsekleri omuzların altında tut.',
      'Karın kaslarını aktif tut.',
      'Bel çökmesini engelle.',
      'Boynu nötr pozisyonda koru.',
    ],
  ),
  ExerciseDetail(
    name: 'Lunge',
    description:
        'Lunge, tek taraflı alt ekstremite kuvveti, denge ve koordinasyon geliştiren etkili bir egzersizdir.',
    targetMuscles: [
      'Quadriceps',
      'Gluteus Maximus',
      'Hamstrings',
      'Calf kasları',
    ],
    commonMistakes: [
      'Öndeki dizin içe kaçması',
      'Gövdenin öne fazla eğilmesi',
      'Adım mesafesinin kısa olması',
      'Denge kaybı',
    ],
    tips: [
      'Öndeki dizini ayak bileği hizasında tut.',
      'Gövdeni dik pozisyonda koru.',
      'Adım mesafeni yeterli ayarla.',
      'Hareketi kontrollü şekilde tamamla.',
    ],
  ),
  ExerciseDetail(
    name: 'Deadlift',
    description:
        'Deadlift, posterior chain kuvvetini geliştiren ileri seviye bileşik bir egzersizdir. Kalça menteşesi ve omurga kontrolü çok önemlidir.',
    targetMuscles: [
      'Hamstrings',
      'Gluteus Maximus',
      'Erector Spinae',
      'Latissimus Dorsi',
    ],
    commonMistakes: [
      'Belin yuvarlanması',
      'Barın vücuttan uzaklaşması',
      'Diz ve kalça zamanlamasının bozulması',
      'Boynun fazla ekstansiyona gitmesi',
    ],
    tips: [
      'Sırtını nötr pozisyonda koru.',
      'Kalçadan menteşe hareketi yap.',
      'Barı vücuda yakın tut.',
      'Hareketi kontrollü başlat ve bitir.',
    ],
  ),
  ExerciseDetail(
    name: 'Shoulder Press',
    description:
        'Shoulder Press, omuz ve üst ekstremite kuvvetini geliştiren temel bir itiş egzersizidir. Core stabilizasyonu ve omuz kontrolü önemlidir.',
    targetMuscles: [
      'Deltoid',
      'Triceps Brachii',
      'Upper Trapezius',
      'Core kasları',
    ],
    commonMistakes: [
      'Belin fazla arkaya kavislenmesi',
      'Dirseklerin kontrolsüz açılması',
      'Ağırlığın öne veya arkaya kaçması',
      'Core stabilitesinin bozulması',
    ],
    tips: [
      'Core bölgesini aktif tut.',
      'Ağırlığı kontrollü şekilde yukarı it.',
      'Bel boşluğunu artırmamaya dikkat et.',
      'Omuz hareketini kontrollü tamamla.',
    ],
  ),
];

ExerciseDetail getExerciseDetailByName(String name) {
  return exerciseDetails.firstWhere(
    (exercise) => exercise.name == name,
    orElse: () => exerciseDetails.first,
  );
}
