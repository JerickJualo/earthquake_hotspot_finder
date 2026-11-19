import { useCallback, useEffect, useMemo, useState } from "react";

import {
  CircleMarker,
  MapContainer,
  Popup,
  TileLayer,
  ZoomControl,
} from "react-leaflet";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import "leaflet/dist/leaflet.css";

import {
  ApiError,
  getClusters,
  getEarthquakes,
  getHealth,
  getProvinceActivity,
  getReadiness,
  getSummary,
} from "./services/api";

const DEFAULT_FILTERS = {
  start_date: "2025-01-01",
  end_date: "2025-12-31",
  min_magnitude: "",
  max_magnitude: "",
  geographic_assignment_status: "",
};

const STATUS_LABELS = {
  assigned: "Province assigned",
  offshore_or_unassigned: "Offshore / unassigned",
  outside_study_scope_candidate: "Outside-scope candidate",
};

const STATUS_COLORS = {
  assigned: "#54d6a0",
  offshore_or_unassigned: "#f2b872",
  outside_study_scope_candidate: "#f27d92",
};

const PHILIPPINES_BOUNDS = [
  [4.2, 116.5],
  [21.6, 127.5],
];

function formatNumber(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return Number(value).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

function formatDateTime(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function errorMessage(error) {
  if (error instanceof ApiError && error.status === 503) {
    return "The API is running, but the database is not ready. Configure PostgreSQL and import the processed dataset to load live dashboard data.";
  }
  return error?.message || "The dashboard could not load data.";
}

function SummaryCard({ label, value, detail, accent = "blue" }) {
  return (
    <article className={`summary-card accent-${accent}`}>
      <p className="summary-label">{label}</p>
      <p className="summary-value">{value}</p>
      <p className="summary-detail">{detail}</p>
    </article>
  );
}

export function FilterBar({ draft, setDraft, onSubmit, onReset, loading }) {
  function update(key, value) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  return (
    <form className="filter-panel" onSubmit={onSubmit}>
      <div className="filter-heading">
        <div>
          <p className="section-kicker">Explore the record set</p>
          <h2>Shared filters</h2>
        </div>
        <span className="filter-note">UTC dates · inclusive range</span>
      </div>
      <div className="filter-grid">
        <label>
          <span>From date</span>
          <input
            type="date"
            value={draft.start_date}
            onChange={(event) => update("start_date", event.target.value)}
          />
        </label>
        <label>
          <span>To date</span>
          <input
            type="date"
            value={draft.end_date}
            onChange={(event) => update("end_date", event.target.value)}
          />
        </label>
        <label>
          <span>Minimum magnitude</span>
          <input
            type="number"
            min="-10"
            max="20"
            step="0.1"
            placeholder="Any"
            value={draft.min_magnitude}
            onChange={(event) => update("min_magnitude", event.target.value)}
          />
        </label>
        <label>
          <span>Maximum magnitude</span>
          <input
            type="number"
            min="-10"
            max="20"
            step="0.1"
            placeholder="Any"
            value={draft.max_magnitude}
            onChange={(event) => update("max_magnitude", event.target.value)}
          />
        </label>
        <label>
          <span>Geographic scope</span>
          <select
            value={draft.geographic_assignment_status}
            onChange={(event) => update("geographic_assignment_status", event.target.value)}
          >
            <option value="">All statuses</option>
            <option value="assigned">Province assigned</option>
            <option value="offshore_or_unassigned">Offshore / unassigned</option>
            <option value="outside_study_scope_candidate">Outside-scope candidates</option>
          </select>
        </label>
        <div className="filter-actions">
          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "Refreshing…" : "Apply filters"}
          </button>
          <button className="quiet-button" type="button" onClick={onReset} disabled={loading}>
            Reset
          </button>
        </div>
      </div>
    </form>
  );
}

function DistributionBars({ items, labelKey, valueKey, color = "blue", emptyText }) {
  if (!items?.length) return <p className="empty-state">{emptyText || "No distribution is available."}</p>;
  const fill = color === "coral" ? "#ff8f8f" : color === "teal" ? "#66d9c2" : "#6db5ff";
  return (
    <div className="recharts-box distribution-chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={items} layout="vertical" margin={{ top: 0, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="rgba(190, 211, 236, 0.09)" horizontal={false} />
          <XAxis type="number" allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: "#8f9eb2", fontSize: 10 }} />
          <YAxis type="category" dataKey={labelKey} width={92} axisLine={false} tickLine={false} tick={{ fill: "#8f9eb2", fontSize: 10 }} />
          <Tooltip
            cursor={{ fill: "rgba(190, 211, 236, 0.06)" }}
            contentStyle={{ background: "#172438", border: "1px solid rgba(190, 211, 236, 0.18)", borderRadius: 8, color: "#e7edf5", fontSize: 12 }}
            formatter={(value) => [formatNumber(value), "Records"]}
          />
          <Bar dataKey={valueKey} fill={fill} radius={[0, 5, 5, 0]} barSize={12} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function MonthlyChart({ items }) {
  if (!items?.length) return <p className="empty-state">No monthly activity is available.</p>;
  return (
    <div className="recharts-box monthly-recharts" aria-label="Earthquake records by month">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={items} margin={{ top: 8, right: 4, bottom: 0, left: -18 }}>
          <CartesianGrid stroke="rgba(190, 211, 236, 0.09)" vertical={false} />
          <XAxis dataKey="month" tickFormatter={(value) => value.slice(5)} axisLine={false} tickLine={false} tick={{ fill: "#8f9eb2", fontSize: 10 }} />
          <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fill: "#8f9eb2", fontSize: 10 }} />
          <Tooltip
            cursor={{ fill: "rgba(109, 181, 255, 0.08)" }}
            contentStyle={{ background: "#172438", border: "1px solid rgba(190, 211, 236, 0.18)", borderRadius: 8, color: "#e7edf5", fontSize: 12 }}
            labelFormatter={(label) => `Month: ${label}`}
            formatter={(value) => [formatNumber(value), "Records"]}
          />
          <Bar dataKey="earthquake_count" fill="#6db5ff" radius={[5, 5, 0, 0]} barSize={18} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function LegacyCoordinateMap({ assignments }) {
  const width = 760;
  const height = 390;
  const padding = { top: 28, right: 24, bottom: 46, left: 52 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const minLon = 117;
  const maxLon = 128.5;
  const minLat = 4;
  const maxLat = 22;
  const points = assignments || [];
  const clusterColors = ["#66d9c2", "#f4b860", "#ff7d9d", "#9b8cff", "#6db5ff", "#d7e27e"];

  function x(longitude) {
    return padding.left + ((Number(longitude) - minLon) / (maxLon - minLon)) * plotWidth;
  }

  function y(latitude) {
    return padding.top + (1 - (Number(latitude) - minLat) / (maxLat - minLat)) * plotHeight;
  }

  const validPoints = points.filter(
    (point) => Number.isFinite(Number(point.longitude)) && Number.isFinite(Number(point.latitude)),
  );

  return (
    <div className="map-wrap">
      <svg className="coordinate-map" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Earthquake coordinate map">
        <rect x="0" y="0" width={width} height={height} rx="18" className="map-background" />
        {[4, 8, 12, 16, 20].map((latitude) => (
          <g key={`lat-${latitude}`}>
            <line x1={padding.left} x2={width - padding.right} y1={y(latitude)} y2={y(latitude)} className="map-grid" />
            <text x={padding.left - 10} y={y(latitude) + 4} textAnchor="end" className="map-axis-label">{latitude}°N</text>
          </g>
        ))}
        {[118, 121, 124, 127].map((longitude) => (
          <g key={`lon-${longitude}`}>
            <line x1={x(longitude)} x2={x(longitude)} y1={padding.top} y2={height - padding.bottom} className="map-grid" />
            <text x={x(longitude)} y={height - 18} textAnchor="middle" className="map-axis-label">{longitude}°E</text>
          </g>
        ))}
        <text x={padding.left} y={18} className="map-caption">Philippine region coordinate view</text>
        {validPoints.map((point, index) => {
          const cluster = Number(point.cluster_label);
          const color = clusterColors[Number.isFinite(cluster) ? cluster % clusterColors.length : 0];
          return (
            <circle
              key={`${point.event_id || point.source_event_id}-${index}`}
              cx={x(point.longitude)}
              cy={y(point.latitude)}
              r="4.2"
              fill={color}
              className="map-point"
              opacity="0.82"
            >
              <title>{`${point.source_event_id || "Event"} · cluster ${point.cluster_label}`}</title>
            </circle>
          );
        })}
      </svg>
      <div className="map-legend">
        <span><i className="legend-dot dot-cluster-a" /> Cluster 0</span>
        <span><i className="legend-dot dot-cluster-b" /> Cluster 1</span>
        <span className="map-count">{validPoints.length} plotted records</span>
      </div>
      <p className="map-footnote">Coordinates are plotted from the API response; this view is not a basemap or a hazard boundary.</p>
    </div>
  );
}

function CoordinateMap({ assignments }) {
  const points = assignments || [];
  const clusterColors = ["#66d9c2", "#f4b860", "#ff7d9d", "#9b8cff", "#6db5ff", "#d7e27e"];
  const validPoints = points.filter(
    (point) => Number.isFinite(Number(point.longitude)) && Number.isFinite(Number(point.latitude)),
  );

  return (
    <div className="map-wrap">
      <MapContainer
        className="leaflet-map"
        center={[12.8797, 121.774]}
        zoom={5.5}
        minZoom={5}
        maxZoom={10}
        bounds={PHILIPPINES_BOUNDS}
        maxBounds={PHILIPPINES_BOUNDS}
        maxBoundsViscosity={1}
        worldCopyJump={false}
        scrollWheelZoom
        zoomControl={false}
        preferCanvas
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ZoomControl position="bottomright" />
        {validPoints.map((point, index) => {
          const cluster = Number(point.cluster_label);
          const color = clusterColors[Number.isFinite(cluster) ? cluster % clusterColors.length : 0];
          const magnitude = Number(point.magnitude);
          const radius = Number.isFinite(magnitude) ? Math.max(4, Math.min(10, (magnitude - 3.5) * 2.1)) : 5;
          return (
            <CircleMarker
              key={`${point.event_id || point.source_event_id}-${index}`}
              center={[Number(point.latitude), Number(point.longitude)]}
              radius={radius}
              pathOptions={{ color: "#f5fbff", weight: 1.25, fillColor: color, fillOpacity: 0.86 }}
            >
              <Popup>
                <strong>{point.source_event_id || "Earthquake event"}</strong><br />
                {point.occurred_at ? formatDateTime(point.occurred_at) : "Time unavailable"}<br />
                Magnitude {formatNumber(point.magnitude, 1)} · Depth {point.depth_km === null || point.depth_km === undefined ? "—" : `${formatNumber(point.depth_km, 1)} km`}<br />
                {point.province_name || STATUS_LABELS[point.geographic_assignment_status] || "Unassigned"}<br />
                Cluster {point.cluster_label}<br />
                {Number(point.latitude).toFixed(3)}°N, {Number(point.longitude).toFixed(3)}°E
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>
      <div className="map-legend">
        <span><i className="legend-dot dot-cluster-a" /> Cluster 0</span>
        <span><i className="legend-dot dot-cluster-b" /> Cluster 1</span>
        <span className="map-count">{validPoints.length} plotted records</span>
      </div>
      <p className="map-footnote">The view is constrained to the Philippines geographic extent. Marker size reflects magnitude; color identifies the K-Means cluster. This is not a hazard boundary.</p>
    </div>
  );
}

function ProvinceRanking({ provinces }) {
  const topProvinces = (provinces || []).slice(0, 10);
  const max = Math.max(...topProvinces.map((item) => Number(item.earthquake_count) || 0), 1);
  if (!topProvinces.length) return <p className="empty-state">No province assignments match these filters.</p>;

  return (
    <div className="ranking-list">
      {topProvinces.map((province, index) => (
        <div className="ranking-row" key={province.province_name}>
          <span className="ranking-number">{String(index + 1).padStart(2, "0")}</span>
          <span className="ranking-name">{province.province_name}</span>
          <span className="ranking-bar"><i style={{ width: `${(province.earthquake_count / max) * 100}%` }} /></span>
          <strong>{formatNumber(province.earthquake_count)}</strong>
        </div>
      ))}
    </div>
  );
}

function StatusBreakdown({ counts }) {
  const entries = Object.entries(counts || {});
  if (!entries.length) return <p className="empty-state">No geographic assignment data.</p>;
  const total = entries.reduce((sum, [, value]) => sum + Number(value || 0), 0) || 1;
  return (
    <div className="status-breakdown">
      {entries.map(([status, value]) => (
        <div className="status-item" key={status}>
          <div className="status-item-heading">
            <span><i className="legend-dot" style={{ background: STATUS_COLORS[status] || "#9aabc0" }} /> {STATUS_LABELS[status] || status}</span>
            <strong>{formatNumber(value)}</strong>
          </div>
          <div className="status-track"><i style={{ width: `${(Number(value) / total) * 100}%`, background: STATUS_COLORS[status] || "#9aabc0" }} /></div>
        </div>
      ))}
    </div>
  );
}

function RecentEvents({ events }) {
  if (!events?.length) return <p className="empty-state">No events match these filters.</p>;
  return (
    <div className="table-scroll">
      <table>
        <thead><tr><th>UTC time</th><th>Magnitude</th><th>Depth</th><th>Province / status</th></tr></thead>
        <tbody>
          {events.map((event) => (
            <tr key={event.event_id}>
              <td>{formatDateTime(event.occurred_at)}</td>
              <td><strong>{formatNumber(event.magnitude, 1)}</strong></td>
              <td>{event.depth_km === null ? "—" : `${formatNumber(event.depth_km, 1)} km`}</td>
              <td>{event.province_name || STATUS_LABELS[event.geographic_assignment_status] || "Unassigned"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const INSIGHT_ITEMS = [
  { id: "scope", label: "Scope", short: "SC" },
  { id: "temporal", label: "Monthly", short: "MO" },
  { id: "magnitude", label: "Magnitude", short: "MG" },
  { id: "depth", label: "Depth", short: "DP" },
  { id: "provinces", label: "Provinces", short: "PR" },
  { id: "clusters", label: "Clusters", short: "CL" },
  { id: "records", label: "Records", short: "RE" },
];

export function InsightRail({ active, onSelect }) {
  return (
    <nav className="insight-rail" aria-label="Open analytical views">
      <p className="rail-label">Peek</p>
      {INSIGHT_ITEMS.map((item) => (
        <button
          className={`rail-button ${active === item.id ? "rail-button-active" : ""}`}
          type="button"
          key={item.id}
          aria-label={`Open ${item.label} side peek`}
          aria-pressed={active === item.id}
          onClick={() => onSelect(active === item.id ? null : item.id)}
        >
          <span className="rail-icon">{item.short}</span>
          <span>{item.label}</span>
        </button>
      ))}
    </nav>
  );
}

function InsightPeek({ active, summary, dashboard, onClose }) {
  if (!active) return null;

  const item = INSIGHT_ITEMS.find((entry) => entry.id === active);
  let content;
  if (active === "scope") {
    content = (
      <>
        <p className="panel-copy">Only points intersecting an ADM2 polygon receive a province. Offshore and nearby-country records remain visible as separate statuses.</p>
        <StatusBreakdown counts={summary.geographic_assignment_counts} />
        <div className="mini-callout"><strong>{formatNumber(summary.assigned_province_count)}</strong><span>unique provinces represented in the filtered view</span></div>
      </>
    );
  } else if (active === "temporal") {
    content = <MonthlyChart items={summary.monthly_activity} />;
  } else if (active === "magnitude") {
    content = <DistributionBars items={summary.magnitude_distribution} labelKey="magnitude_bin" valueKey="earthquake_count" color="coral" />;
  } else if (active === "depth") {
    content = <DistributionBars items={summary.depth_distribution} labelKey="depth_bin" valueKey="earthquake_count" color="teal" />;
  } else if (active === "provinces") {
    content = <ProvinceRanking provinces={dashboard.provinces} />;
  } else if (active === "clusters") {
    content = (
      <>
        <div className="cluster-summary-list">{dashboard.clusters.summaries.map((cluster) => <div className="cluster-summary" key={cluster.cluster_label}><span className="cluster-swatch" style={{ background: ["#66d9c2", "#f4b860", "#ff7d9d", "#9b8cff"][cluster.cluster_label % 4] }} /><div><strong>Cluster {cluster.cluster_label}</strong><span>{formatNumber(cluster.record_count)} records - mean M {formatNumber(cluster.mean_magnitude, 2)}</span></div><b>{formatNumber(cluster.percentage_of_clustered_records, 1)}%</b></div>)}</div>
        <p className="small-note">Cluster labels are identifiers, not rankings. K-Means uses projected coordinates only.</p>
      </>
    );
  } else if (active === "records") {
    content = <RecentEvents events={dashboard.events.data} />;
  }

  return (
    <aside className="insight-peek" aria-label={`${item.label} details`}>
      <div className="peek-heading">
        <div><p className="section-kicker">Side peek</p><h2>{item.label}</h2></div>
        <button className="peek-close" type="button" onClick={onClose} aria-label="Close side peek">×</button>
      </div>
      {content}
    </aside>
  );
}

function LandingPage({ onOpenDashboard }) {
  return (
    <section className="landing-page-content">
      <div className="landing-hero">
        <div className="landing-copy">
          <p className="eyebrow">Philippine earthquake analytics</p>
          <h1>Read the pattern.<br /><em>Question the conclusion.</em></h1>
          <p className="intro-copy">Explore where and when earthquake records appear across the Philippines through a transparent, map-first research workspace.</p>
          <button className="primary-button landing-cta" type="button" onClick={onOpenDashboard}>Open Map Dashboard <span aria-hidden="true">→</span></button>
        </div>
        <div className="landing-note">
          <span className="note-icon">i</span>
          <div><strong>Provisional development view</strong><br />The current dashboard uses the USGS 2025 development dataset. It describes records and spatial groupings; it does not predict earthquakes or measure hazard.</div>
        </div>
      </div>

      <div className="landing-highlights" aria-label="Dashboard capabilities">
        <article className="landing-highlight"><span className="highlight-number">01</span><h2>See the geography</h2><p>Keep the Philippines spatial view in focus while the supporting analyses open as side peeks.</p></article>
        <article className="landing-highlight"><span className="highlight-number">02</span><h2>Trace the inputs</h2><p>Follow the imported USGS records, ADM2 province assignments, and source references used by the application.</p></article>
        <article className="landing-highlight"><span className="highlight-number">03</span><h2>Explore carefully</h2><p>Apply shared date, magnitude, and geographic-scope filters before interpreting distributions or clusters.</p></article>
      </div>

      <div className="landing-how">
        <p className="section-kicker">How to use it</p>
        <div className="how-steps"><span><b>Filter</b> choose the record window</span><span><b>Observe</b> inspect the map and side peeks</span><span><b>Question</b> read results as provisional evidence</span></div>
      </div>
    </section>
  );
}

function App() {
  const [page, setPage] = useState(() => (window.location.hash === "#dashboard" ? "dashboard" : "landing"));
  const [draftFilters, setDraftFilters] = useState(DEFAULT_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState(DEFAULT_FILTERS);
  const [dashboard, setDashboard] = useState(null);
  const [backendState, setBackendState] = useState("checking");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeInsight, setActiveInsight] = useState(null);

  const navigateTo = useCallback((nextPage) => {
    const nextHash = nextPage === "dashboard" ? "#dashboard" : window.location.pathname;
    window.history.pushState({}, "", nextHash);
    setPage(nextPage);
    if (nextPage === "landing") setActiveInsight(null);
  }, []);

  useEffect(() => {
    const syncPage = () => setPage(window.location.hash === "#dashboard" ? "dashboard" : "landing");
    window.addEventListener("popstate", syncPage);
    window.addEventListener("hashchange", syncPage);
    return () => {
      window.removeEventListener("popstate", syncPage);
      window.removeEventListener("hashchange", syncPage);
    };
  }, []);

  const loadDashboard = useCallback(async (filters) => {
    setLoading(true);
    setError("");
    try {
      const [health, readiness, summary, provinces, clusters, events] = await Promise.all([
        getHealth(),
        getReadiness(),
        getSummary(filters),
        getProvinceActivity(filters).catch((requestError) => {
          if (requestError instanceof ApiError && requestError.status === 404) return [];
          throw requestError;
        }),
        getClusters(filters),
        getEarthquakes(filters, { page: 1, page_size: 8 }),
      ]);
      setDashboard({ health, readiness, summary, provinces, clusters, events });
      setBackendState("connected");
    } catch (requestError) {
      setBackendState(requestError instanceof ApiError && requestError.status === 503 ? "database-pending" : "unavailable");
      setError(errorMessage(requestError));
      setDashboard(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (page !== "dashboard") return;
    loadDashboard(appliedFilters);
  }, [page, appliedFilters, loadDashboard]);

  const summary = dashboard?.summary;
  const activeRange = useMemo(
    () => `${formatDate(summary?.date_min_utc)} — ${formatDate(summary?.date_max_utc)}`,
    [summary],
  );

  function submitFilters(event) {
    event.preventDefault();
    setAppliedFilters({ ...draftFilters });
  }

  function resetFilters() {
    setDraftFilters(DEFAULT_FILTERS);
    setAppliedFilters(DEFAULT_FILTERS);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand brand-button" type="button" onClick={() => navigateTo("landing")} aria-label="Open Earthquake Hotspot Finder introduction">
          <span className="brand-mark"><span /></span>
          <span><strong>Earthquake</strong> Hotspot Finder</span>
        </button>
        <div className="topbar-meta">
          <button className="header-nav-button" type="button" onClick={() => navigateTo(page === "dashboard" ? "landing" : "dashboard")}>
            {page === "dashboard" ? "Introduction" : "Map Dashboard"}
          </button>
          {page === "dashboard" ? (
          <span className={`connection-pill connection-${backendState}`}>
            <i /> {backendState === "connected" ? "API connected" : backendState === "database-pending" ? "Database pending" : backendState === "checking" ? "Connecting" : "API unavailable"}
          </span>
          ) : <span className="connection-pill connection-connected"><i /> Explore overview</span>}
          <span className="dataset-pill">USGS · 2025 development dataset</span>
        </div>
      </header>

      <main className={`dashboard ${page === "dashboard" ? "dashboard-page" : "landing-page"}`}>
        {page === "landing" ? (
          <LandingPage onOpenDashboard={() => navigateTo("dashboard")} />
        ) : (
          <>
        <section className="dashboard-context-header">
          <div><p className="eyebrow">Map Dashboard</p><h1>Spatial view</h1><p className="intro-copy">The Philippines map stays in place while filters and supporting analyses open around it.</p></div>
          <div className="dashboard-context-note"><span className="note-icon">+</span><span>Use the peek buttons on the map to inspect distributions, province activity, clusters, scope, and records.</span></div>
        </section>
        <section className="dashboard-intro">
          <div>
            <p className="eyebrow">Philippine earthquake analytics</p>
            <h1>Read the pattern.<br /><em>Question the conclusion.</em></h1>
            <p className="intro-copy">A transparent workspace for exploring where and when earthquake records appear across the Philippines.</p>
          </div>
          <div className="intro-note">
            <span className="note-icon">i</span>
            <div><strong>Provisional view</strong><br />This dashboard describes the current development dataset. It does not predict earthquakes or measure hazard.</div>
          </div>
        </section>

        <FilterBar
          draft={draftFilters}
          setDraft={setDraftFilters}
          onSubmit={submitFilters}
          onReset={resetFilters}
          loading={loading}
        />

        {error && (
          <section className="error-banner" role="alert">
            <div><strong>Dashboard data unavailable</strong><p>{error}</p></div>
            <button className="quiet-button" type="button" onClick={() => loadDashboard(appliedFilters)}>Try again</button>
          </section>
        )}

        {loading && !dashboard ? (
          <section className="loading-panel"><div className="spinner" /><p>Loading the analytical view…</p></section>
        ) : dashboard ? (
          <>
            <section className="summary-grid" aria-label="Summary statistics">
              <SummaryCard label="Records in view" value={formatNumber(summary.record_count)} detail={activeRange} accent="blue" />
              <SummaryCard label="Magnitude range" value={`${formatNumber(summary.numeric_summary.magnitude?.min, 1)} — ${formatNumber(summary.numeric_summary.magnitude?.max, 1)}`} detail={`Median ${formatNumber(summary.numeric_summary.magnitude?.median, 1)}`} accent="coral" />
              <SummaryCard label="Provinces represented" value={formatNumber(summary.assigned_province_count)} detail="ADM2 point assignments" accent="green" />
              <SummaryCard label="Spatial clusters" value={`K = ${dashboard.clusters.selected_k}`} detail={`${formatNumber(dashboard.clusters.eligible_record_count)} eligible records`} accent="violet" />
            </section>

            {/* Legacy stacked panels replaced by the map-first side-peek workspace below.
            <section className="content-grid map-grid-section">
              <article className="panel map-panel">
                <div className="panel-heading"><div><p className="section-kicker">Spatial view</p><h2>Where records cluster</h2></div><span className="metric-chip">Silhouette {formatNumber(dashboard.clusters.silhouette_score, 3)}</span></div>
                <CoordinateMap assignments={dashboard.clusters.assignments} />
              </article>
              <article className="panel status-panel">
                <div className="panel-heading"><div><p className="section-kicker">Geographic assignment</p><h2>What the boundary tells us</h2></div></div>
                <p className="panel-copy">Only points intersecting an ADM2 polygon receive a province. Offshore and nearby-country records remain visible as separate statuses.</p>
                <StatusBreakdown counts={summary.geographic_assignment_counts} />
                <div className="mini-callout"><strong>{formatNumber(summary.assigned_province_count)}</strong><span>unique provinces represented in the filtered view</span></div>
              </article>
            </section>

            <section className="content-grid charts-grid">
              <article className="panel chart-panel chart-wide"><div className="panel-heading"><div><p className="section-kicker">Temporal distribution</p><h2>Records by month</h2></div><span className="panel-unit">events / month</span></div><MonthlyChart items={summary.monthly_activity} /></article>
              <article className="panel chart-panel"><div className="panel-heading"><div><p className="section-kicker">Magnitude distribution</p><h2>How strong?</h2></div><span className="panel-unit">records</span></div><DistributionBars items={summary.magnitude_distribution} labelKey="magnitude_bin" valueKey="earthquake_count" color="coral" /></article>
              <article className="panel chart-panel"><div className="panel-heading"><div><p className="section-kicker">Depth distribution</p><h2>How deep?</h2></div><span className="panel-unit">records</span></div><DistributionBars items={summary.depth_distribution} labelKey="depth_bin" valueKey="earthquake_count" color="teal" /></article>
            </section>

            <section className="content-grid lower-grid">
              <article className="panel province-panel"><div className="panel-heading"><div><p className="section-kicker">Provincial activity</p><h2>Most represented provinces</h2></div><span className="panel-unit">assigned records</span></div><ProvinceRanking provinces={dashboard.provinces} /></article>
              <article className="panel cluster-panel"><div className="panel-heading"><div><p className="section-kicker">Model summary</p><h2>K-Means groupings</h2></div><span className="metric-chip">K = {dashboard.clusters.selected_k}</span></div><div className="cluster-summary-list">{dashboard.clusters.summaries.map((cluster) => <div className="cluster-summary" key={cluster.cluster_label}><span className="cluster-swatch" style={{ background: ["#66d9c2", "#f4b860", "#ff7d9d", "#9b8cff"][cluster.cluster_label % 4] }} /><div><strong>Cluster {cluster.cluster_label}</strong><span>{formatNumber(cluster.record_count)} records · mean M {formatNumber(cluster.mean_magnitude, 2)}</span></div><b>{formatNumber(cluster.percentage_of_clustered_records, 1)}%</b></div>)}</div><p className="small-note">Cluster labels are identifiers, not rankings. K-Means uses projected coordinates only.</p></article>
            </section>

            <section className="panel recent-panel"><div className="panel-heading"><div><p className="section-kicker">Record detail</p><h2>Latest records in view</h2></div><span className="panel-unit">sorted by UTC time</span></div><RecentEvents events={dashboard.events.data} /></section>
            */}
            <section className="visual-workspace" aria-label="Spatial view and analytical side peeks">
              <article className="panel map-panel main-map-panel">
                <div className="panel-heading"><div><p className="section-kicker">Spatial view</p><h2>Where records cluster</h2></div><span className="metric-chip">Silhouette {formatNumber(dashboard.clusters.silhouette_score, 3)}</span></div>
                <CoordinateMap assignments={dashboard.clusters.assignments} />
                <div className="map-metrics">
                  <span><strong>{formatNumber(dashboard.clusters.eligible_record_count)}</strong> plotted eligible records</span>
                  <span><strong>{formatNumber(dashboard.clusters.excluded_record_count)}</strong> outside clustering scope</span>
                  <span><strong>K = {dashboard.clusters.selected_k}</strong> selected spatial groups</span>
                </div>
              </article>
              <InsightRail active={activeInsight} onSelect={setActiveInsight} />
              <InsightPeek active={activeInsight} summary={summary} dashboard={dashboard} onClose={() => setActiveInsight(null)} />
            </section>
          </>
        ) : null}
          </>
        )}

        <section className="footer-grid">
          <article className="footer-card"><p className="section-kicker">Sources</p><h2>Trace the inputs</h2><p>Results are built from the imported canonical event records and ADM2 geographic assignments.</p><div className="source-links"><a href="https://earthquake.usgs.gov/earthquakes/search/" target="_blank" rel="noreferrer">USGS Earthquake Catalog ↗</a><a href="https://www.geoboundaries.org/" target="_blank" rel="noreferrer">geoBoundaries ↗</a><a href="https://www.phivolcs.dost.gov.ph/" target="_blank" rel="noreferrer">PHIVOLCS · preferred final source ↗</a></div></article>
          <article className="footer-card disclaimer-card"><p className="section-kicker">Scientific disclaimer</p><h2>Use this as an exploratory lens.</h2><p>These records and clusters are descriptive. They do not establish earthquake prediction, recurrence probability, causation, or provincial hazard. The USGS 2025 results are provisional development results and must be rerun after final research data is inspected and imported.</p></article>
        </section>
      </main>
      <footer className="site-footer"><span>Earthquake Hotspot Finder · Phase 8 dashboard</span><span>Historical dataset-relative view · UTC</span></footer>
    </div>
  );
}

export default App;
