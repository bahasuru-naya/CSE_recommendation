import React, { useState, useEffect, useMemo } from 'react';
import {
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Search,
  Download,
  Loader2,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Database,
  ChevronLeft,
  ChevronRight as ChevronRightIcon,
  Table as TableIcon,
  FileSpreadsheet,
} from 'lucide-react';
import { useDbSchemas, useDbTableData } from '../api/client';

const SCHEMA_BADGE = {
  raw: 'bg-slate-700/60 text-slate-300 border border-slate-600',
  staging: 'bg-amber-950/60 text-amber-300 border border-amber-800/60',
  core: 'bg-blue-950/60 text-blue-300 border border-blue-800/60',
  features: 'bg-violet-950/60 text-violet-300 border border-violet-800/60',
  ml: 'bg-emerald-950/60 text-emerald-300 border border-emerald-800/60',
  app: 'bg-cyan-950/60 text-cyan-300 border border-cyan-800/60',
};

const SCHEMA_HEADER = {
  raw: 'text-slate-400',
  staging: 'text-amber-400',
  core: 'text-blue-400',
  features: 'text-violet-400',
  ml: 'text-emerald-400',
  app: 'text-cyan-400',
};

function formatValue(val) {
  if (val === null || val === undefined) {
    return { display: '—', cls: 'text-slate-600 italic', title: 'NULL' };
  }
  if (typeof val === 'boolean') {
    return val
      ? { display: 'TRUE', cls: 'text-emerald-400 font-semibold text-[11px] bg-emerald-950/40 px-1.5 py-0.5 rounded border border-emerald-800/40', title: 'true' }
      : { display: 'FALSE', cls: 'text-rose-400 font-semibold text-[11px] bg-rose-950/40 px-1.5 py-0.5 rounded border border-rose-800/40', title: 'false' };
  }
  if (typeof val === 'number') {
    return { display: val.toLocaleString(), cls: 'text-slate-200 font-mono text-right', title: String(val) };
  }
  const str = typeof val === 'object' ? JSON.stringify(val) : String(val);
  const truncated = str.length > 70 ? str.slice(0, 70) + '…' : str;
  return { display: truncated, cls: 'text-slate-300', title: str.length > 70 ? str : '' };
}

function Pagination({ page, totalPages, totalRows, pageSize, onPage }) {
  if (totalPages <= 1 && totalRows <= pageSize) return null;
  const from = Math.max(1, (page - 1) * pageSize + 1);
  const to = Math.min(page * pageSize, totalRows);

  const pages = [];
  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, page + 2);
  for (let i = start; i <= end; i++) pages.push(i);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-t border-slate-800 bg-slate-900/90 text-xs text-slate-400">
      <div>
        Showing <span className="text-slate-200 font-medium">{from.toLocaleString()}–{to.toLocaleString()}</span> of{' '}
        <span className="text-slate-200 font-medium">{totalRows.toLocaleString()}</span> rows
      </div>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onPage(page - 1)}
          disabled={page <= 1}
          className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition"
          title="Previous Page"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        {start > 1 && (
          <>
            <button onClick={() => onPage(1)} className="px-2 py-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition">1</button>
            {start > 2 && <span className="text-slate-600">…</span>}
          </>
        )}
        {pages.map((p) => (
          <button
            key={p}
            onClick={() => onPage(p)}
            className={`px-2.5 py-1 rounded font-medium transition ${
              p === page
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            {p}
          </button>
        ))}
        {end < totalPages && (
          <>
            {end < totalPages - 1 && <span className="text-slate-600">…</span>}
            <button onClick={() => onPage(totalPages)} className="px-2 py-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition">{totalPages}</button>
          </>
        )}
        <button
          onClick={() => onPage(page + 1)}
          disabled={page >= totalPages}
          className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition"
          title="Next Page"
        >
          <ChevronRightIcon className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function SchemaTree({ schemas, selectedSchema, selectedTable, onSelect }) {
  const [collapsed, setCollapsed] = useState({});

  const toggleSchema = (schema) => {
    setCollapsed((prev) => ({ ...prev, [schema]: !prev[schema] }));
  };

  if (!schemas || schemas.length === 0) {
    return <p className="text-xs text-slate-500 p-4">No schemas or tables found.</p>;
  }

  return (
    <div className="space-y-1">
      {schemas.map((schemaObj) => {
        const schema = schemaObj.schema;
        const tables = schemaObj.tables || [];
        const isOpen = !collapsed[schema];
        const badgeCls = SCHEMA_BADGE[schema] || 'bg-slate-700 text-slate-300';
        const headerCls = SCHEMA_HEADER[schema] || 'text-slate-400';

        return (
          <div key={schema} className="rounded-lg overflow-hidden">
            <button
              onClick={() => toggleSchema(schema)}
              className={`w-full flex items-center justify-between px-3 py-2 text-left hover:bg-slate-800/60 transition ${headerCls}`}
            >
              <div className="flex items-center gap-2">
                {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                <span className="text-xs font-bold uppercase tracking-wider">{schema}</span>
              </div>
              <span className={`text-[10px] px-1.5 py-0.2 rounded font-semibold ${badgeCls}`}>
                {tables.length}
              </span>
            </button>

            {isOpen && (
              <div className="pl-3 pr-1 py-0.5 space-y-0.5 border-l border-slate-800/80 ml-3.5 my-0.5">
                {tables.map((tbl) => {
                  const tableName = tbl.name;
                  const rowCount = tbl.row_count;
                  const isActive = selectedSchema === schema && selectedTable === tableName;

                  return (
                    <button
                      key={tableName}
                      onClick={() => onSelect(schema, tableName)}
                      className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded text-left transition ${
                        isActive
                          ? 'bg-blue-600 text-white font-medium shadow-sm'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                      }`}
                    >
                      <span className="text-xs truncate flex items-center gap-1.5">
                        <TableIcon className={`w-3 h-3 ${isActive ? 'text-blue-200' : 'text-slate-500'}`} />
                        {tableName}
                      </span>
                      {rowCount != null && rowCount >= 0 && (
                        <span className={`text-[11px] ml-2 shrink-0 font-mono ${isActive ? 'text-blue-100' : 'text-slate-500'}`}>
                          {Number(rowCount).toLocaleString()}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function DataTable({ schema, table, rowCountEstimate }) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [sortCol, setSortCol] = useState(null);
  const [sortDir, setSortDir] = useState('desc');

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 350);
    return () => clearTimeout(t);
  }, [search]);

  // Reset state when switching table
  useEffect(() => {
    setPage(1);
    setSearch('');
    setDebouncedSearch('');
    setSortCol(null);
    setSortDir('desc');
  }, [schema, table]);

  const { data, isLoading, isFetching, refetch } = useDbTableData(
    schema, table, page, pageSize, debouncedSearch, sortCol, sortDir
  );

  // Normalize columns list: backend returns [{'name': 'col', 'type': 'type'}] or ['col1']
  const columns = useMemo(() => {
    if (!data?.columns) return [];
    return data.columns.map((c) => {
      if (typeof c === 'object' && c !== null) {
        return { name: c.name, type: c.type || '' };
      }
      return { name: String(c), type: '' };
    });
  }, [data?.columns]);

  // Normalize rows: backend returns 'data' key or 'rows'
  const rows = useMemo(() => {
    if (data?.data && Array.isArray(data.data)) return data.data;
    if (data?.rows && Array.isArray(data.rows)) return data.rows;
    return [];
  }, [data]);

  const totalRows = data?.total ?? data?.total_rows ?? (rowCountEstimate || rows.length);
  const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));

  const handleSort = (colName) => {
    if (sortCol === colName) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortCol(colName);
      setSortDir('asc');
    }
    setPage(1);
  };

  const handleExportCSV = () => {
    if (!rows.length || !columns.length) return;
    const colNames = columns.map((c) => c.name);
    const csvRows = [
      colNames.join(','),
      ...rows.map((row) =>
        colNames
          .map((c) => {
            const val = row[c];
            if (val === null || val === undefined) return '';
            const str = typeof val === 'object' ? JSON.stringify(val) : String(val);
            return str.includes(',') || str.includes('"') || str.includes('\n')
              ? `"${str.replace(/"/g, '""')}"`
              : str;
          })
          .join(',')
      ),
    ].join('\n');

    const blob = new Blob([csvRows], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${schema}_${table}_page${page}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 overflow-hidden">
      {/* Top Table Header */}
      <div className="px-5 py-3.5 border-b border-slate-800 bg-slate-900 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs uppercase font-semibold tracking-wider text-slate-400 bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
            {schema}
          </span>
          <span className="text-slate-500">/</span>
          <span className="text-base font-bold text-white tracking-wide">{table}</span>
          <span className="text-xs text-slate-400 ml-1">
            ({totalRows.toLocaleString()} rows)
          </span>
          {isFetching && <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400 ml-1" />}
        </div>

        {/* Toolbar */}
        <div className="flex items-center gap-2.5">
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search in table..."
              className="w-full bg-slate-850 border border-slate-700 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 transition"
            />
          </div>

          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="bg-slate-850 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500 transition"
          >
            <option value={25}>25 / page</option>
            <option value={50}>50 / page</option>
            <option value={100}>100 / page</option>
          </select>

          <button
            onClick={handleExportCSV}
            disabled={!rows.length}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-750 border border-slate-700 text-xs text-slate-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition"
            title="Download current rows as CSV"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            <span>CSV</span>
          </button>

          <button
            onClick={() => refetch()}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-750 border border-slate-700 text-slate-400 hover:text-white transition"
            title="Refresh Table"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Table Container */}
      <div className="flex-1 overflow-auto min-h-0 bg-slate-950/40">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500 mb-3" />
            <p className="text-xs">Loading {schema}.{table}...</p>
          </div>
        ) : columns.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <Database className="w-10 h-10 mb-2 opacity-30" />
            <p className="text-sm font-medium text-slate-400">No columns found</p>
            <p className="text-xs text-slate-500 mt-1">This table might be empty or restricted.</p>
          </div>
        ) : rows.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-slate-500">
            <Search className="w-10 h-10 mb-2 opacity-30" />
            <p className="text-sm font-medium text-slate-400">No matching records found</p>
            {debouncedSearch && (
              <p className="text-xs text-slate-500 mt-1">
                Try clearing search filter: "<span className="text-slate-300">{debouncedSearch}</span>"
              </p>
            )}
          </div>
        ) : (
          <table className="w-full text-xs text-left border-collapse">
            <thead className="sticky top-0 z-10 bg-slate-900 border-b border-slate-800 shadow-sm">
              <tr>
                {columns.map((col) => {
                  const isSorted = sortCol === col.name;
                  return (
                    <th
                      key={col.name}
                      onClick={() => handleSort(col.name)}
                      className="py-2.5 px-3 font-semibold text-slate-300 uppercase tracking-wider text-[11px] whitespace-nowrap cursor-pointer hover:bg-slate-800 hover:text-white transition select-none group"
                    >
                      <div className="flex items-center gap-1.5">
                        <span>{col.name}</span>
                        {col.type && (
                          <span className="text-[9px] font-normal lowercase text-slate-500 group-hover:text-slate-400">
                            {col.type.replace('character varying', 'varchar')}
                          </span>
                        )}
                        <span className="ml-0.5">
                          {isSorted ? (
                            sortDir === 'asc' ? (
                              <ArrowUp className="w-3 h-3 text-blue-400" />
                            ) : (
                              <ArrowDown className="w-3 h-3 text-blue-400" />
                            )
                          ) : (
                            <ArrowUpDown className="w-3 h-3 text-slate-600 opacity-0 group-hover:opacity-100 transition" />
                          )}
                        </span>
                      </div>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {rows.map((row, idx) => (
                <tr
                  key={row.id ?? idx}
                  className="hover:bg-slate-850/60 transition group"
                >
                  {columns.map((col) => {
                    const rawVal = row[col.name];
                    const { display, cls, title } = formatValue(rawVal);
                    return (
                      <td
                        key={col.name}
                        className={`py-2 px-3 whitespace-nowrap max-w-xs truncate ${cls}`}
                        title={title || undefined}
                      >
                        {display}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination Footer */}
      {!isLoading && (
        <Pagination
          page={page}
          totalPages={totalPages}
          totalRows={totalRows}
          pageSize={pageSize}
          onPage={setPage}
        />
      )}
    </div>
  );
}

export default function DatabaseExplorer() {
  const { data: rawSchemas, isLoading: schemasLoading, refetch: refetchSchemas } = useDbSchemas();
  const [selectedSchema, setSelectedSchema] = useState(null);
  const [selectedTable, setSelectedTable] = useState(null);

  // Normalize schemas into a predictable array: [{ schema: 'core', tables: [{ name: 'dim_security', row_count: 291 }] }]
  const schemas = useMemo(() => {
    if (!rawSchemas) return [];
    if (Array.isArray(rawSchemas)) return rawSchemas;
    return Object.entries(rawSchemas).map(([schemaName, tablesObj]) => ({
      schema: schemaName,
      tables: Object.entries(tablesObj || {}).map(([tblName, tblInfo]) => ({
        name: tblName,
        row_count: tblInfo?.row_count ?? 0,
      })),
    }));
  }, [rawSchemas]);

  // Default select first available table on load
  useEffect(() => {
    if (!selectedSchema && !selectedTable && schemas.length > 0) {
      // Prefer core or app schema if present
      const preferred = schemas.find((s) => s.schema === 'core') || schemas.find((s) => s.schema === 'app') || schemas[0];
      if (preferred && preferred.tables && preferred.tables.length > 0) {
        setSelectedSchema(preferred.schema);
        setSelectedTable(preferred.tables[0].name);
      }
    }
  }, [schemas, selectedSchema, selectedTable]);

  const handleSelect = (schema, table) => {
    setSelectedSchema(schema);
    setSelectedTable(table);
  };

  // Find row count estimate for current table
  const rowCountEstimate = useMemo(() => {
    if (!schemas || !selectedSchema || !selectedTable) return 0;
    const s = schemas.find((item) => item.schema === selectedSchema);
    if (!s) return 0;
    const t = (s.tables || []).find((item) => item.name === selectedTable);
    return t?.row_count ?? 0;
  }, [schemas, selectedSchema, selectedTable]);

  return (
    <div className="space-y-4">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2.5">
            <Database className="w-6 h-6 text-blue-500" />
            Database Explorer
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Directly browse, query, search, and export data across all 6 PostgreSQL &amp; TimescaleDB medallion layers
          </p>
        </div>

        <button
          onClick={() => refetchSchemas()}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-850 hover:bg-slate-800 border border-slate-700 text-xs text-slate-300 hover:text-white transition"
          title="Reload Schema Tree"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Tree</span>
        </button>
      </div>

      {/* Explorer Workspace */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col lg:flex-row h-[78vh] shadow-xl">
        {/* Left Sidebar: Schema Tree */}
        <aside className="w-full lg:w-72 bg-slate-900 border-b lg:border-b-0 lg:border-r border-slate-800 flex flex-col shrink-0">
          <div className="px-4 py-3 border-b border-slate-800 bg-slate-900/90 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Lakehouse Layers
            </span>
            <span className="text-[11px] text-slate-500 font-mono">
              {schemas.reduce((sum, s) => sum + (s.tables?.length || 0), 0)} tables
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-2">
            {schemasLoading ? (
              <div className="flex flex-col items-center justify-center py-12 text-slate-500">
                <Loader2 className="w-5 h-5 animate-spin text-blue-500 mb-2" />
                <span className="text-xs">Loading schemas...</span>
              </div>
            ) : (
              <SchemaTree
                schemas={schemas}
                selectedSchema={selectedSchema}
                selectedTable={selectedTable}
                onSelect={handleSelect}
              />
            )}
          </div>
        </aside>

        {/* Right Content: Data Table */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden bg-slate-950/40">
          {!selectedSchema || !selectedTable ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 p-8">
              <Database className="w-16 h-16 mb-3 text-slate-700" />
              <h3 className="text-base font-semibold text-slate-300 mb-1">Select a Table</h3>
              <p className="text-xs text-slate-500 text-center max-w-sm">
                Pick any table from the layers on the left to inspect its live contents, apply full-text searches, and export CSV snapshots.
              </p>
            </div>
          ) : (
            <DataTable
              key={`${selectedSchema}.${selectedTable}`}
              schema={selectedSchema}
              table={selectedTable}
              rowCountEstimate={rowCountEstimate}
            />
          )}
        </main>
      </div>
    </div>
  );
}
