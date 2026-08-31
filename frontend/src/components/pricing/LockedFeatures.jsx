import { PRO_LOCKED } from "../../lib/pricing";

export default function LockedFeatures() {
  return (
    <ul className="plan-locked" aria-label="Pro features locked on Free">
      {PRO_LOCKED.map((item) => (
        <li key={item}>Locked · {item}</li>
      ))}
    </ul>
  );
}
