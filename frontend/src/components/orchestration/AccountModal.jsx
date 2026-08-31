import { AnimatePresence, motion } from "motion/react";
import { useOrchestration } from "../../context/OrchestrationContext";

export default function AccountModal() {
  const {
    showAccount,
    setShowAccount,
    accountMode,
    setAccountMode,
    accountEmail,
    setAccountEmail,
    accountPassword,
    setAccountPassword,
    accountError,
    setAccountError,
    accountBusy,
    user,
    registerAccount,
    loginAccount,
    logoutAccount,
  } = useOrchestration();

  const title = user ? "Account" : accountMode === "register" ? "Create account" : "Sign in";

  return (
    <AnimatePresence>
      {showAccount && (
        <motion.div
          className="orch-overlay"
          role="presentation"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setShowAccount(false);
          }}
        >
          <motion.div
            className="orch-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="account-title"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
          >
            <div className="orch-modal-head">
              <div>
                <p className="orch-kicker">Account</p>
                <h2 id="account-title">{title}</h2>
                <p>
                  Usage limits belong to your signed-in account, not this
                  browser tab.
                </p>
              </div>
              <button
                type="button"
                className="orch-icon-btn"
                aria-label="Close account dialog"
                onClick={() => setShowAccount(false)}
              >
                ×
              </button>
            </div>

            {user ? (
              <div className="orch-modal-card">
                <p className="orch-kicker">Signed in</p>
                <h3>{user.email}</h3>
                <button
                  type="button"
                  className="orch-btn ghost"
                  onClick={() => {
                    logoutAccount();
                    setShowAccount(false);
                  }}
                >
                  Sign out
                </button>
              </div>
            ) : (
              <form
                className="orch-modal-card"
                onSubmit={(event) => {
                  event.preventDefault();
                  if (accountMode === "register") registerAccount();
                  else loginAccount();
                }}
              >
                {accountError ? (
                  <p className="orch-auth-error" role="alert">
                    {accountError}
                  </p>
                ) : null}
                <label className="orch-label" htmlFor="account-email">
                  Email
                </label>
                <input
                  id="account-email"
                  type="email"
                  autoComplete="email"
                  value={accountEmail}
                  onChange={(event) => {
                    setAccountEmail(event.target.value);
                    setAccountError("");
                  }}
                  required
                />
                <label className="orch-label" htmlFor="account-password">
                  Password
                </label>
                <input
                  id="account-password"
                  type="password"
                  autoComplete={
                    accountMode === "register" ? "new-password" : "current-password"
                  }
                  value={accountPassword}
                  onChange={(event) => {
                    setAccountPassword(event.target.value);
                    setAccountError("");
                  }}
                  minLength={8}
                  required
                />
                <button type="submit" className="orch-btn" disabled={accountBusy}>
                  {accountBusy
                    ? "Working…"
                    : accountMode === "register"
                      ? "Create account"
                      : "Sign in"}
                </button>
                <button
                  type="button"
                  className="orch-btn ghost"
                  onClick={() => {
                    setAccountMode(
                      accountMode === "register" ? "login" : "register"
                    );
                    setAccountError("");
                  }}
                >
                  {accountMode === "register"
                    ? "Have an account? Sign in"
                    : "Create an account"}
                </button>
              </form>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
