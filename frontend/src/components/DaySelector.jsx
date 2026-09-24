export default function DaySelector({ selectedDay, onChange }) {
  return (
    <div className="flex flex-wrap gap-2">
      {Array.from({ length: 10 }, (_, index) => index + 1).map(
        (day) => (
          <button
            key={day}
            onClick={() => onChange(day)}
            className={`
              rounded-lg px-4 py-2 text-sm font-medium
              transition
              ${
                selectedDay === day
                  ? "bg-blue-600 text-white shadow"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }
            `}
          >
            Day {day}
          </button>
        )
      )}
    </div>
  );
}