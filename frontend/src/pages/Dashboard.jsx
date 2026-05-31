import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { getDashboardSummary, getDashboardAssets, getDashboardTopRisks } from "../services/api";

const RISK_COLORS = {
  CRITICAL: "#dc2626",
  HIGH: "#ea580c",
  MEDIUM: "#ca8a04",
  LOW: "#16a34a",
};

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [assets, setAssets] = useState([]);
  const [topRisks, setTopRisks] = useState([]);

  const fetchData = async () => {
    try {
      const [sumRes, assetsRes, risksRes] = await Promise.all([
        getDashboardSummary(),
        getDashboardAssets(),
        getDashboardTopRisks(),
      ]);
      setSummary(sumRes.data);
      setAssets(assetsRes.data);
      setTopRisks(risksRes.data);
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, []);

  const riskCounts = assets.reduce(
    (acc, a) => {
      acc[a.risk_level] = (acc[a.risk_level] || 0) + 1;
      return acc;
    },
    {}
  );

  const chartData = ["CRITICAL", "HIGH", "MEDIUM", "LOW"].map((level) => ({
    name: level,
    count: riskCounts[level] || 0,
  }));

  if (!summary) {
    return (
      <div className="flex items-center justify-center h-96 text-gray-400">
        Loading dashboard...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Assets" value={summary.total_assets} color="text-blue-400" />
        <StatCard title="Critical Risks" value={summary.critical_risks} color="text-red-400" />
        <StatCard title="High Risks" value={summary.high_risks} color="text-orange-400" />
        <StatCard title="Exposure Score" value={`${summary.overall_score}/100`} color="text-yellow-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData}>
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{ backgroundColor: "#1f2937", border: "1px solid #374151", borderRadius: "8px" }}
                labelStyle={{ color: "#f3f4f6" }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={index} fill={RISK_COLORS[entry.name]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">Top Attack Paths</h3>
          <div className="space-y-2 max-h-[250px] overflow-y-auto">
            {topRisks.length === 0 && (
              <p className="text-gray-400 text-sm">No risks found</p>
            )}
            {topRisks.map((risk, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className="w-2 h-2 rounded-full bg-red-500 shrink-0" />
                <span className="text-gray-300 font-medium">{risk.hostname}</span>
                <span className="text-gray-500">-</span>
                <span className="text-gray-400">{risk.finding}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="p-6 border-b border-gray-700">
          <h3 className="text-lg font-semibold text-white">Asset Inventory</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
                <th className="px-6 py-3">Hostname</th>
                <th className="px-6 py-3">Risk Level</th>
                <th className="px-6 py-3">Risk Score</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((asset) => (
                <tr
                  key={asset.hostname}
                  className="border-b border-gray-700/50 hover:bg-gray-700/30 cursor-pointer"
                  onClick={() => (window.location.href = `/assets/${asset.hostname}`)}
                >
                  <td className="px-6 py-4 text-white font-medium">{asset.hostname}</td>
                  <td className="px-6 py-4">
                    <span
                      className="px-2 py-1 rounded-full text-xs font-semibold text-white"
                      style={{ backgroundColor: RISK_COLORS[asset.risk_level] }}
                    >
                      {asset.risk_level}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-300">{asset.score}</td>
                </tr>
              ))}
              {assets.length === 0 && (
                <tr>
                  <td colSpan="3" className="px-6 py-8 text-center text-gray-400">
                    No assets found. Ingest assets to get started.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, color }) {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <p className="text-gray-400 text-sm mb-1">{title}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
