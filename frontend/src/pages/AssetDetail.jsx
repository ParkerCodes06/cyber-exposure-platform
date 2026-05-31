import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { getScan } from "../services/api";

const RISK_COLORS = {
  CRITICAL: "#dc2626",
  HIGH: "#ea580c",
  MEDIUM: "#ca8a04",
  LOW: "#16a34a",
};

export default function AssetDetail() {
  const { hostname } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchScan = async () => {
      try {
        const res = await getScan(hostname);
        setData(res.data);
      } catch (err) {
        console.error("Scan failed:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchScan();
  }, [hostname]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-gray-400">
        Scanning {hostname}...
      </div>
    );
  }

  if (!data || data.error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-400 text-lg mb-4">Asset not found</p>
        <Link to="/" className="text-blue-400 hover:text-blue-300">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const report = data.report;
  const riskLevel = report.risk_overview.level;
  const riskScore = report.risk_overview.score;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/" className="text-gray-400 hover:text-white transition-colors">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </Link>
        <div>
          <h2 className="text-2xl font-bold text-white">{hostname}</h2>
          <p className="text-gray-400 text-sm">Security Assessment Report</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <p className="text-gray-400 text-sm mb-1">Risk Level</p>
          <span
            className="px-3 py-1 rounded-full text-sm font-semibold text-white"
            style={{ backgroundColor: RISK_COLORS[riskLevel] }}
          >
            {riskLevel}
          </span>
        </div>
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <p className="text-gray-400 text-sm mb-1">Risk Score</p>
          <p className="text-3xl font-bold text-yellow-400">{riskScore}</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <p className="text-gray-400 text-sm mb-1">Total Findings</p>
          <p className="text-3xl font-bold text-blue-400">
            {report.critical_findings.length}
          </p>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Executive Summary</h3>
        <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-line">
          {report.executive_summary}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Attack Paths</h3>
          <div className="space-y-2">
            {report.attack_paths.length === 0 && (
              <p className="text-gray-400 text-sm">No attack paths identified</p>
            )}
            {report.attack_paths.map((path, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-red-500 shrink-0" />
                <span className="text-gray-300">{path}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Remediation Plan</h3>
          <div className="space-y-2">
            {report.remediation_plan.length === 0 && (
              <p className="text-gray-400 text-sm">No remediation actions required</p>
            )}
            {report.remediation_plan.map((plan, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-green-500 shrink-0" />
                <span className="text-gray-300">{plan}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
