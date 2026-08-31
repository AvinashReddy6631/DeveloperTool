import { AnimatePresence, motion } from "motion/react";
import { PLAN_FEATURES } from "../../lib/pricing";
import ProBadge from "./ProBadge";
import "./pricing.css";

export default function UpgradeModal({ open, onClose }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="upgrade-overlay"
          role="presentation"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) onClose();
          }}
        >
          <motion.div
            className="upgrade-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="upgrade-title"
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
          >
            <ProBadge plan="pro" />
            <h2 id="upgrade-title">Pro is positioned, not billed.</h2>
            <p>
              Pro is the expanded surface for this product. Checkout and plan
              changes are not implemented. This dialog does not charge a card
              and does not move you onto Pro.
            </p>

            <div className="upgrade-ledger">
              <section className="upgrade-block">
                <h3>Selected plan</h3>
                <p>Pro · recommended when billing exists</p>
              </section>
              <section className="upgrade-block">
                <h3>Subscription summary</h3>
                <ul>
                  {PLAN_FEATURES.pro.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>
              <section className="upgrade-block">
                <h3>Payment information</h3>
                <p>No card fields. Payment processing is not part of this product yet.</p>
              </section>
              <section className="upgrade-block">
                <h3>Billing information</h3>
                <p>No invoice, tax, or billing address is collected here.</p>
              </section>
              <section className="upgrade-block upgrade-total">
                <h3>Total</h3>
                <p>$0 · no charge</p>
              </section>
            </div>

            <p className="upgrade-notice">
              No payment processing. No fake purchase success.
            </p>
            <div className="upgrade-actions">
              <button type="button" className="orch-btn di-btn di-btn-primary" onClick={onClose}>
                Stay on Free
              </button>
              <button type="button" className="orch-btn ghost di-btn di-btn-ghost" onClick={onClose}>
                Close
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
