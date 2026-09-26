export default function DaySelector({
  selectedDay,
  onChange,
  disabled = false,
  forecastStart = "2026-09-24",
}) {
  const getDayDate = (dayIndex) => {
    try {
      const parts = String(forecastStart || "2026-09-24").split("-");
      let baseDate;
      if (parts.length === 3) {
        baseDate = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
      } else {
        baseDate = new Date();
      }
      baseDate.setDate(baseDate.getDate() + (dayIndex - 1));
      return baseDate.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });
    } catch (e) {
      return `+${dayIndex - 1}d`;
    }
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-10 gap-2">
      {Array.from({ length: 10 }, (_, index) => {
        const day = index + 1;
        const dateStr = getDayDate(day);
        const isSelected = selectedDay === day;
        const isExtendedRange = day >= 6;

        return (
          <button
            key={day}
            type="button"
            disabled={disabled}
            aria-pressed={isSelected}
            onClick={() => onChange(day)}
            className={`
              relative flex flex-col items-center justify-center p-2.5 rounded-xl border text-center transition-all duration-150 cursor-pointer
              ${
                isSelected
                  ? "bg-blue-600 text-white border-blue-600 shadow-md ring-2 ring-blue-400/30 font-bold"
                  : "bg-white text-slate-700 border-slate-200 hover:border-slate-300 hover:bg-slate-50"
              }
              disabled:cursor-not-allowed disabled:opacity-60
            `}
          >
            <div className="flex items-center gap-1.5">
              <span
                className={`text-xs font-bold ${
                  isSelected ? "text-white" : "text-slate-900"
                }`}
              >
                Day {day}
              </span>
              {isExtendedRange && (
                <span
                  title="Medium-range forecast (higher uncertainty)"
                  className={`h-1.5 w-1.5 rounded-full ${
                    isSelected ? "bg-amber-300" : "bg-amber-400"
                  }`}
                />
              )}
            </div>
            <span
              className={`text-[11px] mt-0.5 font-medium ${
                isSelected ? "text-blue-100" : "text-slate-500"
              }`}
            >
              {dateStr}
            </span>
          </button>
        );
      })}
    </div>
  );
}