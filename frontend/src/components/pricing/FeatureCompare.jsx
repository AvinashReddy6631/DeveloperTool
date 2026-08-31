import { COMPARISON_ROWS } from "../../lib/pricing";

export default function FeatureCompare() {
  return (
    <div className="orch-table-wrap">
      <table className="plan-compare">
        <caption className="plan-caption">
          Free versus Pro feature comparison
        </caption>
        <thead>
          <tr>
            <th>Capability</th>
            <th>Free</th>
            <th>Pro</th>
          </tr>
        </thead>
        <tbody>
          {COMPARISON_ROWS.map((row) => (
            <tr key={row.feature}>
              <td>{row.feature}</td>
              <td>{row.free}</td>
              <td>{row.pro}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
