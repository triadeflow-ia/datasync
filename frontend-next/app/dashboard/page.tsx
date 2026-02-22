"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { Modal } from "@/components/Modal";
import {
  apiJobsList,
  apiJobGet,
  apiJobUpload,
  apiJobPreview,
  apiJobReport,
  apiJobDownload,
  apiJobRetry,
  apiJobDelete,
  clearToken,
} from "@/lib/api";

type Job = {
  id: string;
  status: string;
  filename_original: string;
  created_at: string;
  error_message?: string;
};

type ReportData = {
  total_rows: number;
  rows_output: number;
  pct_with_email: number;
  pct_with_phone: number;
  created_at: string;
};

export default function DashboardPage() {
  const { token, isReady, setToken } = useAuth();
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [uploadError, setUploadError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [currentStatus, setCurrentStatus] = useState("");
  const [polling, setPolling] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  // Modal state
  const [previewData, setPreviewData] = useState<Record<string, string>[] | null>(null);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [deleteJobId, setDeleteJobId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadJobs = useCallback(async () => {
    try {
      const data = await apiJobsList({ limit: 50 });
      setJobs(data.jobs);
    } catch {
      setJobs([]);
    }
  }, []);

  useEffect(() => {
    if (!isReady) return;
    if (!token) {
      router.replace("/login");
      return;
    }
    loadJobs();
  }, [isReady, token, router, loadJobs]);

  useEffect(() => {
    if (!currentJobId || !polling) return;
    const t = setInterval(async () => {
      try {
        const job = await apiJobGet(currentJobId);
        setCurrentStatus(job.status);
        if (job.status === "done" || job.status === "failed") {
          setPolling(false);
          setCurrentJobId(null);
          loadJobs();
        }
      } catch {
        setPolling(false);
        setCurrentJobId(null);
      }
    }, 2000);
    return () => clearInterval(t);
  }, [currentJobId, polling, loadJobs]);

  async function processFile(file: File) {
    if (!file.name.match(/\.(xlsx|csv)$/i)) {
      setUploadError("Aceito apenas .xlsx ou .csv");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setUploadError("Arquivo excede 10 MB");
      return;
    }
    setUploadError("");
    setUploading(true);
    try {
      const data = await apiJobUpload(file);
      setCurrentJobId(data.id);
      setCurrentStatus(data.status);
      setPolling(true);
      loadJobs();
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : "Erro no upload");
    } finally {
      setUploading(false);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    await processFile(file);
    e.target.value = "";
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) processFile(file);
  }

  function handleLogout() {
    clearToken();
    setToken(null);
    router.replace("/login");
  }

  async function handlePreview(jobId: string) {
    try {
      const data = await apiJobPreview(jobId);
      setPreviewData(data);
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : "Erro ao carregar preview");
    }
  }

  async function handleReport(jobId: string) {
    try {
      const data = await apiJobReport(jobId);
      setReportData(data);
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : "Erro ao carregar report");
    }
  }

  async function handleDelete() {
    if (!deleteJobId) return;
    setDeleting(true);
    try {
      await apiJobDelete(deleteJobId);
      setDeleteJobId(null);
      loadJobs();
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : "Erro ao deletar");
    } finally {
      setDeleting(false);
    }
  }

  function statusClass(s: string) {
    if (s === "queued") return "statusBadge statusQueued";
    if (s === "processing") return "statusBadge statusProcessing";
    if (s === "done") return "statusBadge statusDone";
    if (s === "failed") return "statusBadge statusFailed";
    return "statusBadge statusQueued";
  }

  if (!isReady || !token) {
    return (
      <div className="container">
        <p>Carregando...</p>
      </div>
    );
  }

  const previewColumns = previewData && previewData.length > 0 ? Object.keys(previewData[0]) : [];

  return (
    <div className="container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h1 style={{ margin: 0 }}>FlowBase</h1>
        <button type="button" className="btn btnSecondary" onClick={handleLogout}>
          Sair
        </button>
      </div>
      <p style={{ color: "#8b949e", marginBottom: "1.5rem" }}>
        Envie uma planilha XLSX ou CSV para converter ao formato GoHighLevel.
      </p>

      {/* Upload zone */}
      <div className="card">
        <div
          className={`uploadZone ${dragOver ? "dragOver" : ""}`}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.csv"
            onChange={handleUpload}
            style={{ display: "none" }}
            disabled={uploading}
          />
          <p style={{ margin: 0 }}>
            {uploading ? (
              "Enviando..."
            ) : dragOver ? (
              <strong>Solte o arquivo aqui</strong>
            ) : (
              <>
                <strong>Clique aqui</strong> ou arraste um arquivo (.xlsx ou .csv, max 10 MB)
              </>
            )}
          </p>
        </div>
        {uploadError && <p className="error">{uploadError}</p>}
        {currentJobId && polling && (
          <p style={{ marginTop: "1rem", color: "#8b949e" }}>
            Processando: <span className={statusClass(currentStatus)}>{currentStatus}</span>
          </p>
        )}
      </div>

      {/* Jobs list */}
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Seus jobs ({jobs.length})</h3>
        {jobs.length === 0 ? (
          <p style={{ color: "#8b949e" }}>Nenhum job ainda. Envie uma planilha acima.</p>
        ) : (
          jobs.map((j) => (
            <div key={j.id} className="jobItem">
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {j.filename_original}
                </div>
                <div style={{ fontSize: "0.85rem", color: "#8b949e" }}>
                  {new Date(j.created_at).toLocaleString("pt-BR")}
                </div>
                {j.status === "failed" && j.error_message && (
                  <div className="jobError">{j.error_message}</div>
                )}
              </div>
              <span className={statusClass(j.status)}>{j.status}</span>
              <div style={{ display: "flex", gap: "0.5rem", flexShrink: 0 }}>
                {j.status === "done" && (
                  <>
                    <button type="button" className="btn btnSecondary" onClick={() => handlePreview(j.id)}>
                      Preview
                    </button>
                    <button type="button" className="btn btnSecondary" onClick={() => handleReport(j.id)}>
                      Report
                    </button>
                    <button type="button" className="btn btnSecondary" onClick={() => apiJobDownload(j.id)}>
                      Baixar CSV
                    </button>
                  </>
                )}
                {j.status === "failed" && (
                  <button
                    type="button"
                    className="btn btnSecondary"
                    onClick={async () => {
                      try {
                        await apiJobRetry(j.id);
                        loadJobs();
                      } catch (e) {
                        setUploadError(e instanceof Error ? e.message : String(e));
                      }
                    }}
                  >
                    Retry
                  </button>
                )}
                <button type="button" className="btn btnDanger" onClick={() => setDeleteJobId(j.id)}>
                  Deletar
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Preview Modal */}
      <Modal open={previewData !== null} onClose={() => setPreviewData(null)} title="Preview (20 primeiras linhas)" wide>
        {previewData && previewData.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <table className="previewTable">
              <thead>
                <tr>
                  {previewColumns.map((col) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewData.map((row, i) => (
                  <tr key={i}>
                    {previewColumns.map((col) => (
                      <td key={col} title={row[col] || ""}>{row[col] || ""}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p style={{ color: "#8b949e" }}>Sem dados de preview.</p>
        )}
      </Modal>

      {/* Report Modal */}
      <Modal open={reportData !== null} onClose={() => setReportData(null)} title="Relatorio de Processamento">
        {reportData && (
          <div className="reportGrid">
            <div className="reportMetric">
              <div className="value">{reportData.total_rows}</div>
              <div className="label">Linhas no arquivo</div>
            </div>
            <div className="reportMetric">
              <div className="value">{reportData.rows_output}</div>
              <div className="label">Linhas no CSV GHL</div>
            </div>
            <div className="reportMetric">
              <div className="value">{reportData.pct_with_email}%</div>
              <div className="label">Com email</div>
            </div>
            <div className="reportMetric">
              <div className="value">{reportData.pct_with_phone}%</div>
              <div className="label">Com telefone</div>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal open={deleteJobId !== null} onClose={() => setDeleteJobId(null)} title="Confirmar exclusao">
        <p>Tem certeza que deseja deletar este job? Os arquivos associados tambem serao removidos.</p>
        <div className="confirmActions">
          <button type="button" className="btn btnSecondary" onClick={() => setDeleteJobId(null)}>
            Cancelar
          </button>
          <button type="button" className="btn btnDanger" onClick={handleDelete} disabled={deleting}>
            {deleting ? "Deletando..." : "Deletar"}
          </button>
        </div>
      </Modal>
    </div>
  );
}
