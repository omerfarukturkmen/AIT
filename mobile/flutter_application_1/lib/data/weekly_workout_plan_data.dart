import '../models/workout_plan_model.dart';

const List<DailyWorkoutPlan> weeklyWorkoutPlan = [
  DailyWorkoutPlan(
    day: 'Pazartesi',
    focus: 'Lower Body Focus',
    isRestDay: false,
    exercises: [
      WorkoutExercise(
        name: 'Squat',
        sets: '3 set',
        reps: '12 tekrar',
        note: 'Diz ve ayak hizasını koru.',
      ),
      WorkoutExercise(
        name: 'Lunge',
        sets: '3 set',
        reps: '10 tekrar',
        note: 'Gövdeyi dik tut.',
      ),
      WorkoutExercise(
        name: 'Plank',
        sets: '3 set',
        reps: '40 sn',
        note: 'Core bölgesini aktif tut.',
      ),
    ],
  ),
  DailyWorkoutPlan(
    day: 'Salı',
    focus: 'Upper Body Control',
    isRestDay: false,
    exercises: [
      WorkoutExercise(
        name: 'Push-up',
        sets: '3 set',
        reps: '10 tekrar',
        note: 'Kalça ve omuz hizasını koru.',
      ),
      WorkoutExercise(
        name: 'Shoulder Press',
        sets: '3 set',
        reps: '12 tekrar',
        note: 'Bel boşluğunu artırmamaya dikkat et.',
      ),
    ],
  ),
  DailyWorkoutPlan(
    day: 'Çarşamba',
    focus: 'Recovery Day',
    isRestDay: true,
    exercises: [],
  ),
  DailyWorkoutPlan(
    day: 'Perşembe',
    focus: 'Full Body Stability',
    isRestDay: false,
    exercises: [
      WorkoutExercise(
        name: 'Squat',
        sets: '3 set',
        reps: '12 tekrar',
        note: 'İniş fazını kontrollü yap.',
      ),
      WorkoutExercise(
        name: 'Push-up',
        sets: '3 set',
        reps: '8 tekrar',
        note: 'Core stabilitesini koru.',
      ),
      WorkoutExercise(
        name: 'Plank',
        sets: '3 set',
        reps: '45 sn',
        note: 'Bel çökmesini engelle.',
      ),
    ],
  ),
  DailyWorkoutPlan(
    day: 'Cuma',
    focus: 'Posterior Chain',
    isRestDay: false,
    exercises: [
      WorkoutExercise(
        name: 'Deadlift',
        sets: '3 set',
        reps: '10 tekrar',
        note: 'Sırtını nötr pozisyonda tut.',
      ),
      WorkoutExercise(
        name: 'Lunge',
        sets: '3 set',
        reps: '10 tekrar',
        note: 'Denge kontrolüne odaklan.',
      ),
    ],
  ),
  DailyWorkoutPlan(
    day: 'Cumartesi',
    focus: 'Core & Mobility',
    isRestDay: false,
    exercises: [
      WorkoutExercise(
        name: 'Plank',
        sets: '4 set',
        reps: '35 sn',
        note: 'Nefes kontrolünü koru.',
      ),
      WorkoutExercise(
        name: 'Squat',
        sets: '2 set',
        reps: '15 tekrar',
        note: 'Mobilite odaklı çalış.',
      ),
    ],
  ),
  DailyWorkoutPlan(
    day: 'Pazar',
    focus: 'Rest Day',
    isRestDay: true,
    exercises: [],
  ),
];