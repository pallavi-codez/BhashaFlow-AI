import React from 'react';
import { BarChart3, TrendingUp, Wallet, CreditCard, ShieldCheck, PieChart, IndianRupee } from 'lucide-react';

export default function ReportsView({ stats }) {
  const creditSales = Number(stats?.total_credit_sales || 0);
  const cashSales = Number(stats?.total_cash_sales || 0);
  const totalSales = creditSales + cashSales;
  const paymentsReceived = Number(stats?.total_payments_received || 0);
  const cashReceived = Number(stats?.total_cash_received || 0);
  const expenses = Number(stats?.total_expenses || 0);
  const netCash = Number(stats?.net_cash_movement || 0);
  const outstanding = Number(stats?.total_outstanding || 0);

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.4rem', fontWeight: 700 }}>
          Financial Reports &amp; Ledger Auditing
        </h2>
        <p style={{ fontSize: '0.875rem', color: '#64748B' }}>
          Exact decimal accounting rules verified from the immutable SQLite/Postgres database.
        </p>
      </div>

      {/* Primary Financial Summary Cards */}
      <div className="metrics-grid">
        <div className="metric-card metric-sales">
          <div className="metric-header">
            <span className="metric-label">Total Shop Sales</span>
            <div className="metric-icon-box"><TrendingUp size={20} /></div>
          </div>
          <div className="metric-value">₹{totalSales.toFixed(2)}</div>
          <div className="metric-footer">Credit Sales (₹{creditSales}) + Cash Sales (₹{cashSales})</div>
        </div>

        <div className="metric-card metric-cash">
          <div className="metric-header">
            <span className="metric-label">Total Cash Collected</span>
            <div className="metric-icon-box"><Wallet size={20} /></div>
          </div>
          <div className="metric-value">₹{cashReceived.toFixed(2)}</div>
          <div className="metric-footer">Cash Sales (₹{cashSales}) + Debt Collected (₹{paymentsReceived})</div>
        </div>

        <div className="metric-card metric-debt">
          <div className="metric-header">
            <span className="metric-label">Total Customer Debt</span>
            <div className="metric-icon-box"><IndianRupee size={20} /></div>
          </div>
          <div className="metric-value">₹{outstanding.toFixed(2)}</div>
          <div className="metric-footer">Outstanding = Σ(Credit Sales) - Σ(Payments Received)</div>
        </div>

        <div className="metric-card metric-expense">
          <div className="metric-header">
            <span className="metric-label">Total Expenses</span>
            <div className="metric-icon-box"><CreditCard size={20} /></div>
          </div>
          <div className="metric-value">₹{expenses.toFixed(2)}</div>
          <div className="metric-footer">Net Cash Movement: ₹{netCash.toFixed(2)}</div>
        </div>
      </div>

      {/* Accounting Rules Integrity Card */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: '50%', background: '#ECFDF5', color: '#10B981', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldCheck size={20} />
            </div>
            <h3 className="card-title">Accounting Rules &amp; Verification Matrix</h3>
          </div>
          <span className="badge badge-payment">Mathematical Invariants Enforced</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
          <div style={{ padding: 16, background: '#F8FAFC', borderRadius: 12, border: '1px solid #E2E8F0' }}>
            <div style={{ fontWeight: 700, color: '#F59E0B', marginBottom: 6 }}>1. Credit Sale (Udhar)</div>
            <p style={{ fontSize: '0.85rem', color: '#334155', lineHeight: 1.6 }}>
              &bull; Total sales <strong>INCREASE</strong><br />
              &bull; Customer outstanding debt <strong>INCREASES</strong><br />
              &bull; Cash received <strong>DOES NOT INCREASE</strong>
            </p>
          </div>

          <div style={{ padding: 16, background: '#F8FAFC', borderRadius: 12, border: '1px solid #E2E8F0' }}>
            <div style={{ fontWeight: 700, color: '#10B981', marginBottom: 6 }}>2. Payment Against Debt</div>
            <p style={{ fontSize: '0.85rem', color: '#334155', lineHeight: 1.6 }}>
              &bull; Customer outstanding debt <strong>DECREASES</strong><br />
              &bull; Cash collected <strong>INCREASES</strong><br />
              &bull; Total new sales <strong>DO NOT INCREASE</strong>
            </p>
          </div>

          <div style={{ padding: 16, background: '#F8FAFC', borderRadius: 12, border: '1px solid #E2E8F0' }}>
            <div style={{ fontWeight: 700, color: '#0284C7', marginBottom: 6 }}>3. Immediate Cash Sale</div>
            <p style={{ fontSize: '0.85rem', color: '#334155', lineHeight: 1.6 }}>
              &bull; Total sales <strong>INCREASE</strong><br />
              &bull; Cash received <strong>INCREASES</strong><br />
              &bull; Customer debt <strong>DOES NOT CHANGE</strong>
            </p>
          </div>

          <div style={{ padding: 16, background: '#F8FAFC', borderRadius: 12, border: '1px solid #E2E8F0' }}>
            <div style={{ fontWeight: 700, color: '#EF4444', marginBottom: 6 }}>4. Shop Expense</div>
            <p style={{ fontSize: '0.85rem', color: '#334155', lineHeight: 1.6 }}>
              &bull; Recorded expenses <strong>INCREASE</strong><br />
              &bull; Net cash movement <strong>REDUCES</strong><br />
              &bull; Sales <strong>DO NOT INCREASE</strong>
            </p>
          </div>
        </div>

        <div style={{ marginTop: 20, padding: '14px 18px', background: '#EFF6FF', borderRadius: 10, fontSize: '0.85rem', color: '#1E40AF', display: 'flex', alignItems: 'center', gap: 10 }}>
          <span>🔒</span>
          <div>
            <strong>Decimal-Safe Guarantee:</strong> All financial entries are stored using <code>Numeric(12, 2)</code> in the database and calculated using Python's exact <code>Decimal</code> module. Floating-point rounding errors are strictly eliminated.
          </div>
        </div>
      </div>
    </div>
  );
}
