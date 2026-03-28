import { useState, type ChangeEvent } from "react";
import { parseImage } from "../services/api";

export function ImageUploadPlaceholder() {
  const [msg, setMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setMsg(null);
    try {
      const res = await parseImage(file);
      setMsg(JSON.stringify(res, null, 2));
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card card-muted">
      <h2>Multimodal image parse</h2>
      <p className="small">
        Backend uses Kimi vision via GMI (<code>KIMI_VISION_MODEL</code>). Upload a squad screenshot; JSON
        parsing may vary by image quality.
      </p>
      <input type="file" accept="image/*" onChange={onFile} disabled={loading} />
      {msg && <pre className="code small-pre">{msg}</pre>}
    </section>
  );
}
