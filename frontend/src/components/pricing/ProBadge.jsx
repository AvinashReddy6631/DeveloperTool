import "./pricing.css";

export default function ProBadge({ plan = "free" }) {
  const isPro = plan === "pro";
  return (
    <span className={`plan-badge ${isPro ? "is-pro" : "is-free"}`}>
      {isPro ? "Pro" : "Free"}
    </span>
  );
}
