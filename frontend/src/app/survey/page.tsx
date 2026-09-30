"use client";
import Link from "next/link";
import { useMemo, useState } from "react";
import { Alert, ErrorState, Field, LoadingRows, useLoad } from "@/components/ui";
import { api, ApiError } from "@/lib/api";
import { DISTRICTS, type Question } from "@/lib/types";

const SCALE = ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"];
const TITLES: Record<string, string> = { PU: "Usefulness", PEOU: "Ease of use", TR: "Trust", CO: "Cost", AC: "Access", WA: "Your plans" };

export default function Survey() {
  const qs = useLoad(() => api<Question[]>("survey"), []);
  const [startedAt] = useState(() => Date.now());
  const [step, setStep] = useState(0);
  const [consent, setConsent] = useState(false);
  const [meta, setMeta] = useState({ respondent_type: "", age_band: "", gender: "", district: "", uses_mobile_money: "" });
  const [ans, setAns] = useState<Record<number, number>>({});
  const [err, setErr] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const groups = useMemo(() => { const m = new Map<string, Question[]>(); for (const q of qs.data ?? []) m.set(q.construct, [...(m.get(q.construct) ?? []), q]); return [...m.entries()]; }, [qs.data]);
  const total = groups.length + 1;
  if (done) return <div className="mid page center"><h1>Thank you! 🙏</h1><p className="lead muted">Your anonymous answers will help us understand how small businesses in Kabul view mobile money.</p><Link className="btn" href="/">Back to Bazar.af</Link></div>;
  function next() {
    setErr(null); setMissing(false);
    if (step === 0) { if (!consent) return setErr("Please tick the consent box to continue."); if (!meta.respondent_type) return setErr("Tell us whether you are a seller, buyer or other."); }
    else if (groups[step - 1][1].some((q) => !ans[q.id])) return setMissing(true);
    setStep(step + 1); window.scrollTo({ top: 0 });
  }
  async function submit() {
    if (groups[step - 1][1].some((q) => !ans[q.id])) return setMissing(true);
    setBusy(true); setErr(null);
    try {
      await api("survey/responses", { method: "POST", body: { consent: true, respondent_type: meta.respondent_type, age_band: meta.age_band || null, gender: meta.gender || null, district: meta.district || null,
        uses_mobile_money: meta.uses_mobile_money === "" ? null : meta.uses_mobile_money === "yes", completion_seconds: Math.round((Date.now() - startedAt) / 1000), answers: Object.entries(ans).map(([question_id, value]) => ({ question_id: Number(question_id), value })) } });
      setDone(true);
    } catch (x) { setErr(x instanceof ApiError ? x.message : "Could not submit"); } finally { setBusy(false); }
  }
  return (
    <div className="mid page">
      <h1 style={{ fontSize: "2.4rem" }}>Mobile money survey</h1>
      {qs.loading ? <LoadingRows /> : qs.error ? <ErrorState error={qs.error} retry={qs.reload} /> : groups.length === 0 ? <Alert>The survey is not open yet.</Alert> : (<>
        <div className="steps" role="progressbar" aria-valuemin={1} aria-valuemax={total} aria-valuenow={step + 1} aria-label="Survey progress">{Array.from({ length: total }, (_, i) => <span key={i} className={i <= step ? "on" : ""} />)}</div>
        {err && <Alert kind="bad">{err}</Alert>}
        {step === 0 ? (<div className="stack">
          <p className="muted">This survey is part of a university capstone study. It takes about 5 minutes, is <strong>anonymous</strong> and voluntary. We do not collect your name, phone number or IP address with your answers.</p>
          <div className="opt"><input id="consent" type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} /><label htmlFor="consent">I am 18 or older and agree to take part. I understand my answers are anonymous and used for research.</label></div>
          <Field id="rt" label="I am mainly a…"><select id="rt" value={meta.respondent_type} onChange={(e) => setMeta({ ...meta, respondent_type: e.target.value })}><option value="">Select…</option><option value="seller">Business owner / seller</option><option value="buyer">Customer / buyer</option><option value="other">Other</option></select></Field>
          <div className="grid g2">
            <Field id="age" label="Age (optional)"><select id="age" value={meta.age_band} onChange={(e) => setMeta({ ...meta, age_band: e.target.value })}><option value="">Prefer not to say</option>{["18-24", "25-34", "35-44", "45-54", "55+"].map((a) => <option key={a}>{a}</option>)}</select></Field>
            <Field id="gen" label="Gender (optional)"><select id="gen" value={meta.gender} onChange={(e) => setMeta({ ...meta, gender: e.target.value })}><option value="">Prefer not to say</option><option value="female">Female</option><option value="male">Male</option></select></Field>
            <Field id="dist" label="District (optional)"><select id="dist" value={meta.district} onChange={(e) => setMeta({ ...meta, district: e.target.value })}><option value="">Select…</option>{DISTRICTS.map((d) => <option key={d}>{d}</option>)}</select></Field>
            <Field id="mm" label="Do you use mobile money now?"><select id="mm" value={meta.uses_mobile_money} onChange={(e) => setMeta({ ...meta, uses_mobile_money: e.target.value })}><option value="">Select…</option><option value="yes">Yes</option><option value="no">No</option></select></Field>
          </div>
        </div>) : (<div className="stack">
          <h2 style={{ fontSize: "1.6rem" }}>{TITLES[groups[step - 1][0]] ?? groups[step - 1][0]}</h2>
          {missing && <Alert kind="bad">Please answer every statement on this page.</Alert>}
          {groups[step - 1][1].map((q) => (
            <fieldset key={q.id} className="card" style={{ border: undefined }}>
              <legend className="sr">{q.text_en}</legend>
              <p><strong>{q.text_en}</strong></p>
              <div className="likert">{SCALE.map((s, i) => (
                <label key={s}><input type="radio" name={`q${q.id}`} value={i + 1} checked={ans[q.id] === i + 1} onChange={() => setAns({ ...ans, [q.id]: i + 1 })} /><strong>{i + 1}</strong><span className="small"> {s}</span></label>
              ))}</div>
            </fieldset>
          ))}
        </div>)}
        <div className="row between" style={{ marginTop: 28 }}>
          <button className="btn quiet" disabled={step === 0} onClick={() => setStep(step - 1)}>Back</button>
          {step < total - 1 ? <button className="btn" onClick={next}>Next</button> : <button className="btn" disabled={busy} onClick={submit}>{busy ? "Submitting…" : "Submit"}</button>}
        </div>
      </>)}
    </div>
  );
}
