import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Link, NavLink, Route, Routes } from "react-router-dom";
import "./index.css";
import AuditPage from "./pages/AuditPage";
import EntitiesPage from "./pages/EntitiesPage";
import InvestigationDetail from "./pages/InvestigationDetail";
import InvestigationList from "./pages/InvestigationList";
import NewInvestigation from "./pages/NewInvestigation";
import ReportPrint from "./pages/ReportPrint";

function Layout({ children }: { children: React.ReactNode }) {
  const nav = ({ isActive }: { isActive: boolean }) =>
    `rounded-md px-3 py-1.5 text-sm ${isActive ? "bg-indigo-50 font-medium text-indigo-700" : "text-slate-600 hover:bg-slate-100"}`;
  return (
    <>
      <header className="no-print border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-4 py-3">
          <Link to="/" className="text-lg font-bold text-slate-900">
            🔎 Lacak
          </Link>
          <nav className="flex gap-1">
            <NavLink to="/" end className={nav}>
              Investigasi
            </NavLink>
            <NavLink to="/entities" className={nav}>
              Daftar Entitas
            </NavLink>
            <NavLink to="/audit" className={nav}>
              Log Audit
            </NavLink>
          </nav>
          <Link to="/new" className="btn-primary ml-auto">
            + Investigasi baru
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
      <footer className="no-print mx-auto max-w-6xl px-4 pb-8 text-xs text-slate-500">
        Lacak hanya memproses data publik melalui API resmi, file import, dan riset web publik.
        Gunakan secara sah, proporsional, dan sesuai UU Pelindungan Data Pribadi (UU 27/2022).
      </footer>
    </>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/investigations/:id/report" element={<ReportPrint />} />
        <Route
          path="*"
          element={
            <Layout>
              <Routes>
                <Route path="/" element={<InvestigationList />} />
                <Route path="/new" element={<NewInvestigation />} />
                <Route path="/investigations/:id" element={<InvestigationDetail />} />
                <Route path="/entities" element={<EntitiesPage />} />
                <Route path="/audit" element={<AuditPage />} />
              </Routes>
            </Layout>
          }
        />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
