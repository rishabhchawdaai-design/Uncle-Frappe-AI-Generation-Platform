#!/usr/bin/env python3
"""
AI Generation CLI — extend main.py with generation commands.
"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


async def cmd_generate(prompt, style="", width=1024, height=1024, provider=""):
    """Generate an image from a text prompt through the unified SDK."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.generate(prompt, style=style, width=width, height=height, provider=provider or None)
    print(f"\n  Provider:    {result.provider}")
    print(f"  Status:      {result.status}")
    print(f"  Latency:     {result.latency_ms}ms")
    print(f"  Format:      {result.output_format}")
    if result.output_path:
        print(f"  Saved to:    {result.output_path}")
    if result.output_url:
        print(f"  URL:         {result.output_url}")
    if result.error:
        print(f"  Error:       {result.error}")
    return result


async def cmd_video(prompt, duration=4.0, width=1280, height=720):
    """Generate a video from a text prompt through the unified SDK."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.generate_video(prompt, duration_secs=duration, width=width, height=height)
    print(f"\n  Provider:    {result.provider}")
    print(f"  Status:      {result.status}")
    print(f"  Latency:     {result.latency_ms}ms")
    if result.output_url:
        print(f"  URL:         {result.output_url}")
    if result.error:
        print(f"  Error:       {result.error}")
    return result


async def cmd_text(prompt, model="", system_prompt=""):
    """Generate a text/chat response through the unified provider layer (keyless Pollinations + key-based backends)."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.generate_text(prompt, model=model, system_prompt=system_prompt, timeout_secs=90)
    print(f"\n  Provider:    {result.provider}")
    print(f"  Status:      {result.status}")
    print(f"  Latency:     {result.latency_ms}ms")
    if result.success:
        print(f"  Answer:      {result.metadata.get('text', '')[:1000]}")
    if result.error:
        print(f"  Error:       {result.error}")
    return result


async def cmd_graph_sync():
    """Synchronize the capability graph from the live registries."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    report = ai.sync_capability_graph()
    print(f"\n  Capability Graph Sync")
    print(f"  New nodes:       {report['new_nodes']}")
    print(f"  New edges:       {report['new_edges']}")
    print(f"  Total nodes:     {report['total_nodes']}")
    print(f"  Total edges:     {report['total_edges']}")
    return report


async def cmd_compat_stats():
    """Show compatibility matrix statistics."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.compat_get_stats()
    print("\n  Compatibility Matrix (COMPATIBILITY_MATRIX.md)")
    print(f"  Entries:      {stats['total_entries']}")
    print(f"  Models:       {stats['total_models']}")
    print(f"  Runtimes:     {stats['total_runtimes']} catalogued / {stats['catalogued_runtimes']} total")
    print(f"  By category:  {stats['by_category']}")
    print(f"  By evidence:  {stats['by_evidence']}")
    return stats


async def cmd_compat_lookup(model_id, runtime_id, hardware_id="all"):
    """Look up a model x runtime x hardware combination."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    entry = ai.compat_lookup(model_id, runtime_id, hardware_id)
    if entry is None:
        print(f"\n  No entry for {model_id} x {runtime_id} x {hardware_id}")
        return None
    print(f"\n  {model_id} x {runtime_id} x {hardware_id}")
    print(f"  Score: {entry.get('performance_score')}  Evidence: {entry.get('evidence')}")
    print(f"  Quantization: {entry.get('quantization')}  Context: {entry.get('max_context')}")
    return entry


async def cmd_compat_runtimes(model_id, hardware_id=""):
    """List best-scoring runtimes for a model."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    results = ai.compat_find_runtimes(model_id, hardware_id)
    print(f"\n  Compatible runtimes for {model_id}:")
    for r in results:
        print(f"  - {r['runtime_id']:18s} score={r['performance_score']} "
              f"hw={r['hardware_id']} evidence={r['evidence']}")
    return results


async def cmd_compat_models(category, hardware_id=""):
    """List best-scoring models for a runtime category."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    results = ai.compat_find_models(category, hardware_id)
    print(f"\n  Compatible models (category={category or 'all'}):")
    for r in results[:20]:
        print(f"  - {r['model_id']:22s} runtime={r['runtime_id']:16s} "
              f"score={r['performance_score']} evidence={r['evidence']}")
    return results


async def cmd_compat_validate(model_id, runtime_id, hardware_id="all"):
    """Validate an execution path against the compatibility matrix."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = ai.compat_validate_path(model_id, runtime_id, hardware_id)
    status = "VALID" if result["valid"] else "INVALID"
    print(f"\n  [{status}] {model_id} x {runtime_id} x {hardware_id}")
    print(f"  Reason: {result.get('reason', '')}")
    return result


async def cmd_event_classes():
    """List ACOS event taxonomy classes and delivery guarantees."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    classes = ai.list_event_classes()
    print("\n  ACOS Event Taxonomy — Delivery Guarantees\n")
    for name, policy in classes.items():
        print(f"  {name:12s} guarantee={policy['guarantee']:14s} persist={str(policy['persist']):5s} max_attempts={policy['max_attempts']}")
    return classes


async def cmd_event_emit(subject, payload):
    """Emit a durable event (persisted + live fan-out)."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    try:
        import json as _json
        parsed = _json.loads(payload) if payload.startswith(("{", "[")) else payload
    except Exception:
        parsed = payload
    event = ai.emit_durable_event(subject, parsed)
    print(f"\n  Event:       {event['subject']} ({event['event_id']})")
    print(f"  Class:       {event['event_class']} | guarantee={event['guarantee']}")
    print(f"  Status:      {event['status']}")
    return event


async def cmd_event_replay(subject=""):
    """Replay events from the durable log."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    events = ai.replay_events(subject=subject, limit=100)
    print(f"\n  Replayed events{(' for ' + subject) if subject else ''}: {len(events)}\n")
    for e in events:
        print(f"  - [{e['event_class']:8s}] {e['subject']:28s} status={e['status']:12s} attempts={e['attempts']}")
    return events


async def cmd_event_stats():
    """Get durable event log statistics."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_event_log_stats()
    print(f"\n  Durable Event Log: {stats['db_path']}")
    print(f"  Total events:      {stats['total_events']}")
    print(f"  By status:         {stats.get('by_status', {})}")
    print(f"  By class:          {stats.get('by_class', {})}")
    print(f"  DLQ size:          {stats.get('by_status', {}).get('dead_letter', 0)}")
    return stats


async def cmd_event_purge(status="dead_letter"):
    """Purge events by status (default: dead-letter queue)."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    count = ai.purge_events(status=status)
    print(f"\n  Purged {count} events with status='{status}'")
    return count


async def cmd_storage_list():
    """List all storage backends and profiles."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    backends = ai.list_storage_backends()
    print(f"\n  Storage Backends ({len(backends)} total)\n")
    for b in backends:
        icon = "\u2705" if b.get("available") else "\u274c"
        status = b.get("status", "unknown")
        print(f"  {icon} {b['name']:18s}  tasks={','.join(b.get('tasks', [])):24s} status={status}")
    return backends


async def cmd_storage_write(collection, key, value, task="metadata"):
    """Write a record to the selected storage backend."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    try:
        import json as _json
        parsed = _json.loads(value) if value.startswith(("{", "[")) else value
    except Exception:
        parsed = value
    result = ai.storage_write(collection, key, parsed, task=task)
    print(f"\n  Backend:     {result['collection']}/{result['key']}")
    print(f"  Task:        {task}")
    print(f"  Updated:     {result['updated_at']}")
    return result


async def cmd_storage_read(collection, key, task="metadata"):
    """Read a record from the selected storage backend."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = ai.storage_read(collection, key, task=task)
    if not result:
        print(f"\n  Not found: {collection}/{key}")
        return result
    print(f"\n  Key:         {result['key']}")
    print(f"  Value:       {result['value']}")
    print(f"  Metadata:    {result.get('metadata', {})}")
    return result


async def cmd_storage_query(collection, limit=100, task="metadata"):
    """Query records from the selected storage backend."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    rows = ai.storage_query(collection, limit=limit, task=task)
    print(f"\n  Records in '{collection}': {len(rows)}\n")
    for r in rows:
        print(f"  - {r['key']:30s} {str(r['value'])[:80]}")
    return rows


async def cmd_storage_stats():
    """Get storage backend statistics and health."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_storage_stats()
    print(f"\n  Storage backends: {stats['backends_total']} "
          f"(local: {stats['backends_local']}, configured: {stats['backends_configured']})")
    for name, live in stats.get("live", {}).items():
        if isinstance(live, dict):
            print(f"  - {name:16s} records={live.get('records', '?')} "
                  f"collections={live.get('collections', '?')}")
    return stats


async def cmd_local_backends():
    """List the built-in free local backends (no API key required)."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    backends = ai.list_local_backends()
    print(f"\n  Local Backends ({len(backends)} total — free, self-hostable, CPU)\n")
    for b in backends:
        status_icon = "\u2705" if b["available"] else "\u274c"
        print(f"  {status_icon} {b['name']:22s}  {b['description']}")
    return backends


async def cmd_embed(text):
    """Generate a text embedding (384-dim) with the local sentence-transformers backend."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.generate_embedding(text)
    print(f"\n  Provider:    {result.provider}")
    print(f"  Status:      {result.status}")
    print(f"  Latency:     {result.latency_ms}ms")
    if result.success:
        print(f"  Vector dim:  {result.metadata.get('vector_dim')}")
        print(f"  Model:       {result.metadata.get('model')}")
        print(f"  Head:        {result.metadata.get('vector', [])}")
    if result.error:
        print(f"  Error:       {result.error}")
    return result


async def cmd_tts(text, output_path=""):
    """Generate speech with the local Piper backend (CPU, no API key)."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.generate_speech_local(text)
    print(f"\n  Provider:    {result.provider}")
    print(f"  Status:      {result.status}")
    print(f"  Latency:     {result.latency_ms}ms")
    print(f"  Bytes:       {len(result.output_bytes or b'')}")
    if output_path and result.output_bytes:
        from pathlib import Path as _P
        _P(output_path).write_bytes(result.output_bytes)
        print(f"  Saved to:    {output_path}")
    if result.error:
        print(f"  Error:       {result.error}")
    return result


async def cmd_stt(audio_path, model=""):
    """Transcribe an audio file with the local faster-whisper backend (CPU)."""
    from pathlib import Path as _P
    if not _P(audio_path).exists():
        print(f"\n  Error: file not found: {audio_path}")
        return None
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.transcribe_audio(audio_path=audio_path, model=model)
    print(f"\n  Provider:    {result.provider}")
    print(f"  Status:      {result.status}")
    print(f"  Latency:     {result.latency_ms}ms")
    if result.success:
        print(f"  Transcript:  {result.metadata.get('text', '')}")
    if result.error:
        print(f"  Error:       {result.error}")
    return result


async def cmd_translate(text, target_lang="fr", source_lang=""):
    """Translate text locally with Helsinki-NLP opus-mt (CPU)."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.translate_text(text, target_lang=target_lang, source_lang=source_lang)
    print(f"\n  Provider:    {result.provider}")
    print(f"  Status:      {result.status}")
    print(f"  Latency:     {result.latency_ms}ms")
    if result.success:
        print(f"  Translation: {result.metadata.get('text', '')}")
    if result.error:
        print(f"  Error:       {result.error}")
    return result


async def cmd_ocr(image_path):
    """Extract text from an image with Tesseract OCR (CPU)."""
    from pathlib import Path as _P
    if not _P(image_path).exists():
        print(f"\n  Error: file not found: {image_path}")
        return None
    from ai_generation.ocr_engine import DocumentType, OCRRequest
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = ai.ocr_engine.process(
        OCRRequest(document_type=DocumentType.IMAGE, language="en", backend="tesseract"),
        document_data=_P(image_path).read_bytes(),
    )
    print(f"\n  Backend:     {result.backend}")
    print(f"  Status:      {result.metadata.get('status', 'ok')}")
    if result.text:
        print(f"  Text:        {result.text[:2000]}")
    if result.metadata.get("error"):
        print(f"  Error:       {result.metadata['error']}")
    return result


async def cmd_upscale(image_path, output_path=""):
    """Upscale an image 4x locally with Real-ESRGAN (CPU)."""
    from pathlib import Path as _P
    if not _P(image_path).exists():
        print(f"\n  Error: file not found: {image_path}")
        return None
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.upscale_image_local(_P(image_path).read_bytes())
    print(f"\n  Provider:    {result.provider}")
    print(f"  Status:      {result.status}")
    print(f"  Latency:     {result.latency_ms}ms")
    if result.success:
        print(f"  Dimensions:  {result.width}x{result.height}")
        out = output_path or f"./output/upscale_{result.request_id}.png"
        _P(out).parent.mkdir(parents=True, exist_ok=True)
        _P(out).write_bytes(result.output_bytes)
        print(f"  Saved to:    {out}")
    if result.error:
        print(f"  Error:       {result.error}")
    return result


async def cmd_bg_remove(image_path, output_path=""):
    """Remove an image background locally with rembg/u2net (CPU)."""
    from pathlib import Path as _P
    if not _P(image_path).exists():
        print(f"\n  Error: file not found: {image_path}")
        return None
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.remove_background_local(_P(image_path).read_bytes())
    print(f"\n  Provider:    {result.provider}")
    print(f"  Status:      {result.status}")
    print(f"  Latency:     {result.latency_ms}ms")
    if result.success:
        out = output_path or f"./output/bg_removed_{result.request_id}.png"
        _P(out).parent.mkdir(parents=True, exist_ok=True)
        _P(out).write_bytes(result.output_bytes)
        print(f"  Saved to:    {out}  ({result.width}x{result.height})")
    if result.error:
        print(f"  Error:       {result.error}")
    return result


async def cmd_enhance(prompt, style="photorealistic"):
    """Enhance a prompt with cinematic and quality techniques."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = ai.enhance_prompt(prompt, style=style)
    print(f"\n  Original:  {result.original}")
    print(f"  Enhanced:  {result.enhanced}")
    print(f"  Negative:  {result.negative_prompt}")
    print(f"  Style:     {result.style}")
    print(f"  Applied:   {', '.join(result.techniques_applied)}")
    print(f"  Confidence: {result.confidence:.0%}")


async def cmd_providers():
    """List available generation providers with availability status."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    providers = ai.list_providers()
    print(f"\n  AI Generation Providers ({len(providers)} total)\n")
    for p in providers:
        status_icon = "\u2705" if p["available"] else "\u274c"
        print(f"  {status_icon} {p['name']:20s}  type={p['type']:8s}  tier={p['tier']:10s}  models={len(p.get('models', []))}")


async def cmd_benchmarks(prompt="a beautiful landscape"):
    """Run image benchmarks across all providers and show rankings."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    print(f"\n  Running benchmarks with prompt: {prompt}\n")
    from ai_generation.providers.registry import get_registry
    registry = get_registry()
    from ai_generation.providers.base import ProviderType
    results = await ai.benchmark_engine.benchmark_all(registry, prompt, provider_type=ProviderType.IMAGE, runs=1)
    for name, runs in results.items():
        for r in runs:
            status = "\u2705" if r.success else "\u274c"
            print(f"  {status} {name:20s}  latency={r.latency_ms:.0f}ms  cost=${r.cost_estimate:.4f}  error={r.error or 'none'}")
    print(f"\n  Rankings:")
    for s in ai.benchmark_engine.get_rankings():
        print(f"    {s.provider:20s}  score={s.score:.1f}  success={s.success_rate:.0f}%  latency={s.avg_latency_ms:.0f}ms")


async def cmd_providers_list():
    """List known providers from research, including free tier status."""
    from ai_generation.research_agent import ResearchAgent
    ra = ResearchAgent()
    free = ra.get_free_providers()
    all_p = ra.get_known_providers()
    print(f"\n  Known Providers: {len(all_p)} (Free: {len(free)})\n")
    for d in all_p:
        icon = "\u2b50" if d["tier"] == "free" else "\ud83d\udcb0" if d["tier"] == "paid" else "\ud83d\udce6"
        print(f"  {icon} {d['name']:20s}  type={d['provider_type']:8s}  tier={d['tier']:10s}  models={len(d['models'])}")


async def cmd_stats():
    """Print aggregate platform statistics."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_stats()
    print(f"\n  AI Generation Platform Stats\n")
    print(f"  Providers:  {stats['generation']['provider_summary']['total_providers']} total")
    print(f"  Templates:  {stats['prompts']['templates_count']}")
    print(f"  Styles:     {len(stats['prompts']['style_presets'])}")
    print(f"  Benchmarks: {stats['benchmarks']['total_benchmarks']}")
    print(f"  Assets:     {stats['assets']['total_assets']}")
    print(f"  Characters: {stats['characters']['total_characters']}")
    print(f"  Projects:   {stats['projects']['total_projects']}")
    print(f"  Edits:      {stats['image_editing']['total_edits']}")
    print(f"  Videos:     {stats['video_generation']['total_generations']}")
    print(f"  Plans:      {stats['agent_planner']['total_plans']}")


# ── Phase 11 Commands ──

async def cmd_analyze(prompt):
    """Analyze a generation request and recommend providers and workflow."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    analysis = ai.analyze_request(prompt)
    print(f"\n  Request Analysis\n")
    print(f"  Request:   {analysis.original_prompt[:80]}")
    print(f"  Type:      {analysis.request_type.value}")
    print(f"  Media:     {analysis.media_type.value}")
    print(f"  Complexity: {analysis.complexity.value}")
    print(f"  Workflow:  {analysis.suggested_workflow}")
    print(f"  Est Cost:  ${analysis.estimated_total_cost:.6f}")
    print(f"  Est Latency: {analysis.estimated_total_latency_ms:.0f}ms")
    print(f"\n  Recommended Providers:")
    for p in analysis.recommended_providers:
        print(f"    {p['provider']:20s}  score={p['score']}  free={p['free']}")


async def cmd_edit(operation, input_path, prompt="", mask=""):
    """Run an image editing operation on an input file."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.image_editing.edit(operation, input_path, prompt=prompt, mask_path=mask)
    print(f"\n  Edit Result\n")
    print(f"  Operation: {result.operation.value}")
    print(f"  Provider:  {result.provider}")
    print(f"  Status:    {result.status.value}")
    print(f"  Latency:   {result.latency_ms}ms")
    if result.output_url:
        print(f"  URL:       {result.output_url}")
    if result.output_path:
        print(f"  Saved:     {result.output_path}")
    if result.error:
        print(f"  Error:     {result.error}")


async def cmd_video_gen(prompt, duration=4.0, image_path=""):
    """Generate video from text or an input image and print capabilities."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    if image_path:
        result = await ai.video_generation.image_to_video(image_path, prompt=prompt, duration_secs=duration)
    else:
        result = await ai.video_generation.text_to_video(prompt, duration_secs=duration)
    print(f"\n  Video Generation Result\n")
    print(f"  Mode:      {result.mode.value}")
    print(f"  Provider:  {result.provider}")
    print(f"  Status:    {result.status}")
    print(f"  Latency:   {result.latency_ms}ms")
    if result.output_url:
        print(f"  URL:       {result.output_url}")
    if result.error:
        print(f"  Error:     {result.error}")
    print(f"\n  Capabilities Report:")
    caps = ai.video_generation.get_capabilities_report()
    for c in caps:
        note = " [NOT AI VIDEO]" if c.get("not_ai_video") else ""
        print(f"    {c['provider']:20s}  {c['mode']:20s}  supported={c['supported']}{note}")


async def cmd_plan(request):
    """Plan a generation request into agent steps."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    plan = ai.plan_request(request)
    print(f"\n  Agent Plan\n")
    print(f"  Request:   {plan.request[:80]}")
    print(f"  Category:  {plan.category}")
    print(f"  Template:  {plan.workflow_template}")
    print(f"  Providers: {', '.join(plan.recommended_providers)}")
    print(f"  Steps:     {len(plan.steps)}")
    print(f"  Exports:   {', '.join(plan.export_formats)}")
    print(f"\n  Steps:")
    for s in plan.steps:
        dep = f" (depends: {', '.join(s.depends_on)})" if s.depends_on else ""
        print(f"    [{s.step_id:20s}] {s.name}{dep}")
    if plan.prompts:
        print(f"\n  Generated Prompts:")
        for p in plan.prompts:
            print(f"    {p['prompt'][:100]}...")
            if p.get('negative_prompt'):
                print(f"    Neg: {p['negative_prompt'][:80]}...")


async def cmd_character(action, name="", char_id=""):
    """Create, list, or prompt characters for identity consistency."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    if action == "create" and name:
        char = ai.create_character(name)
        print(f"\n  Created character: {char.name} ({char.character_id})")
    elif action == "list":
        chars = ai.character_manager.list_characters()
        print(f"\n  Characters ({len(chars)}):\n")
        for c in chars:
            print(f"    {c['character_id']:15s}  {c['name']:20s}  version={c['version']}")
    elif action == "prompt" and char_id:
        prompt = ai.character_manager.get_consistency_prompt(char_id)
        print(f"\n  Consistency Prompt: {prompt}")
    else:
        print("  Usage: character [create NAME | list | prompt CHAR_ID]")


async def cmd_project(action, name="", proj_id=""):
    """Create or list generation projects."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    if action == "create" and name:
        proj = ai.create_project(name)
        print(f"\n  Created project: {proj.name} ({proj.project_id})")
    elif action == "list":
        projects = ai.project_manager.list_projects()
        print(f"\n  Projects ({len(projects)}):\n")
        for p in projects:
            print(f"    {p['project_id']:15s}  {p['name']:20s}  assets={p['assets_count']}")
    else:
        print("  Usage: project [create NAME | list]")


async def cmd_cinema_dims():
    """List the 14 cinematic benchmark dimensions and weights."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    dims = ai.get_cinema_dimensions()
    print(f"\n  Cinema Benchmark Dimensions ({len(dims)}):\n")
    for d in dims:
        print(f"    {d['name']:30s}  weight={d['weight']:.1f}  {d['description']}")


async def cmd_capabilities():
    """Print the generation capability matrix summary."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    stats = ai.get_capability_matrix()
    print(f"\n  Capability Matrix\n")
    print(f"  Total Models:  {stats['total_models']}")
    print(f"  Providers:     {stats['providers']} ({', '.join(stats['provider_names'])})")
    print(f"  Image Models:  {stats['image_models']}")
    print(f"  Video Models:  {stats['video_models']}")
    print(f"  Editing:       {stats['editing_capable']}")
    print(f"  Free Tier:     {stats['free_tier_models']}")


async def cmd_intel():
    """Show provider intelligence recommendations."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    recs = ai.get_provider_recommendations()
    print(f"\n  Provider Intelligence Recommendations\n")
    for r in recs:
        print(f"    {r['name']:20s}  priority={r['priority']:8s}  score={r['recommendation_score']:.1f}  free={r['free_tier']}")


async def cmd_video_caps():
    """Print the video generation capabilities report."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    report = ai.video_generation.get_capabilities_report()
    print(f"\n  Video Generation Capabilities\n")
    for c in report:
        note = " [NOT AI VIDEO]" if c.get("not_ai_video") else ""
        print(f"    {c['provider']:20s}  {c['mode']:20s}  supported={c['supported']}{note}")
        if c.get("notes"):
            print(f"      Note: {c['notes']}")


# ── Phase 13 Commands ──

async def cmd_agent_generate(request):
    """Run the agent-based generation pipeline for a request."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.agent_generate(request)
    print(f"\n  Agent Generate\n")
    print(f"  Request: {request[:80]}")
    route = result.get("route", {})
    exec_result = result.get("execution", {})
    print(f"  Task Type:   {route.get('task_type', 'unknown')}")
    print(f"  Confidence:  {route.get('confidence', 0):.0%}")
    print(f"  Status:      {exec_result.get('status', 'unknown')}")
    print(f"  Provider:    {exec_result.get('provider', 'none')}")
    print(f"  Layer:       {exec_result.get('layer', 'none')}")
    if exec_result.get("output_url"):
        print(f"  URL:         {exec_result['output_url']}")
    if exec_result.get("error"):
        print(f"  Error:       {exec_result['error']}")
    print(f"\n  Recommended Providers:")
    for p in route.get("recommended_providers", []):
        print(f"    {p['provider']:20s}  model={p.get('model_id', 'n/a')[:30]}  free={p.get('free_tier', False)}")


async def cmd_endpoints():
    """List configured remote execution endpoints."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    endpoints = ai.agent_providers()
    print(f"\n  Remote Execution Endpoints ({len(endpoints)} total)\n")
    for ep in endpoints:
        status = "\u2705" if ep.get("healthy", True) else "\u274c"
        layer = {1: "API", 2: "HF", 3: "Remote", 4: "Browser"}.get(ep.get("layer", 0), "?")
        print(f"  {status} [{layer:6s}] {ep['name']:20s}  verified={ep.get('verified', False)}  free={ep.get('free_tier', False)}  tasks={len(ep.get('supported_tasks', []))}")


async def cmd_health():
    """Run a health check across all configured providers."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.agent_health_check()
    print(f"\n  Provider Health Check\n")
    for name, status in result.items():
        icon = "\u2705" if status.get("healthy", False) else "\u274c"
        latency = f"  {status.get('latency_ms', 0):.0f}ms" if status.get("latency_ms") else ""
        error = f"  {status.get('error', '')}" if status.get("error") else ""
        print(f"  {icon} {name:25s}{latency}{error}")


async def cmd_cap_matrix():
    """Print the agent capability matrix with provider details."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    matrix = ai.agent_capability_matrix()
    print(f"\n  Capability Registry\n")
    print(f"  Total Models: {matrix['total_models']}")
    print(f"  Providers:    {matrix['providers']}")
    print(f"  Tasks:        {matrix['total_tasks']}")
    print(f"  Tasks: {', '.join(matrix['tasks'])}")
    print(f"\n  Provider Details:")
    for name, details in matrix.get('provider_details', {}).items():
        print(f"    {name:20s}  models={details['models']}  free={details['free_tier']}  tasks={len(details['tasks'])}")


async def cmd_discover():
    """Show provider discovery recommendations."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    recs = ai.get_provider_recommendations()
    print(f"\n  Provider Discovery Recommendations\n")
    for r in recs:
        print(f"    {r['name']:20s}  priority={r['priority']:8s}  score={r['recommendation_score']:.1f}  free={r['free_tier']}  status={r['status']}")


async def cmd_health_cycle():
    """Run a persisted provider health cycle (check, auto-disable, auto-re-enable)."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    report = await ai.run_provider_health_cycle()
    print(f"\n  Provider Health Cycle")
    print(f"  Checked:     {len(report['checked_providers'])} providers")
    print(f"  Healthy:     {len(report['healthy'])}")
    print(f"  Unhealthy:   {len(report['unhealthy'])}")
    print(f"  Disabled:    {report['changes']['disabled'] or 'none'}")
    print(f"  Re-enabled:  {report['changes']['re_enabled'] or 'none'}")
    print(f"  Degraded:    {report['changes']['degraded'] or 'none'}")
    for name in report['unhealthy']:
        statuses = {s['provider']: s for s in report['statuses']}
        s = statuses.get(name, {})
        print(f"    -- {name}: {s.get('last_error', '')}")
    print(f"\n  Persisted:   {report['checked_at']}")
    return report


async def cmd_provider_rank(provider_type=""):
    """Refresh and print the ranked provider network (Discovery Registrar)."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    refreshed = ai.refresh_provider_discovery()
    print(f"\n  Discovery registry: {refreshed['path']}")
    print(f"  Generated:   {refreshed['generated_at']}")
    summary = refreshed["summary"]
    print(f"  Providers:   {summary['total_providers']} total, "
          f"{summary['available']} available, {summary['free']} free")
    ranked = ai.get_provider_ranking(provider_type=provider_type)
    print("\n  Ranked providers:")
    for entry in ranked[:12]:
        flag = "OK" if entry["available"] else "--"
        key = "" if (not entry["requires_api_key"] or entry["has_api_key"]) else " (needs key)"
        print(f"    #{entry['rank']:>2} [{flag}] {entry['name']:22s} "
              f"{entry['type']:10s} score={entry['rank_score']:6.2f} "
              f"lat={entry['avg_latency_ms']:.0f}ms{key}")
    return ranked


async def cmd_add_endpoint(name, url):
    """Register a remote execution endpoint by name and URL."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    ep = ai.agent_add_remote_endpoint(name, url)
    print(f"\n  Added remote endpoint: {name}")
    print(f"  URL: {url}")
    print(f"  Type: {ep.get('type', 'api')}")


async def cmd_classify(request):
    """Classify a request into a task type with provider recommendations."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    decision = ai.agent_classify(request)
    print(f"\n  Task Classification\n")
    print(f"  Request:   {request[:80]}")
    print(f"  Task Type: {decision['task_type']}")
    print(f"  Confidence: {decision['confidence']:.0%}")
    print(f"  Reasoning: {decision['reasoning']}")
    if decision.get("alternatives"):
        print(f"  Alternatives: {', '.join(decision['alternatives'])}")
    print(f"\n  Recommended Providers:")
    for p in decision.get("recommended_providers", [])[:5]:
        print(f"    {p['provider']:20s}  model={p.get('model_id', 'n/a')[:30]}  free={p.get('free_tier', False)}")


# ── Phase 14 — AIG-OS Commands ──────────────────────────────────

async def cmd_aigos_status():
    """Show AIG-OS orchestrator status."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    status = ai.aigos_status()
    registry = status["registry"]
    print(f"\n  AIG-OS Status: {'Initialized' if status['initialized'] else 'Not initialized'}")
    print(f"  Total Agents: {registry['total_agents']}")
    print(f"  Healthy: {registry['healthy']}")
    print(f"\n  Agents:")
    for name, stats in registry.get("agents", {}).items():
        print(f"    {name:20s}  status={stats['status']:8s}  tasks={stats['total_tasks']}  success={stats['successful']}")

async def cmd_aigos_agents():
    """List all AIG-OS agents."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    agents = ai.aigos_agents()
    print(f"\n  AIG-OS Agents ({len(agents)}):")
    for a in agents:
        print(f"    {a['agent_name']:20s}  status={a['status']:8s}  tasks={a['total_tasks']}")

async def cmd_aigos_execute(request):
    """Execute a request through the AIG-OS pipeline."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = ai.aigos_execute(request)
    print(f"\n  AIG-OS Execution Result:")
    print(f"    Request: {result.get('data', {}).get('request', request)[:60]}")
    plan = result.get("data", {}).get("plan", {})
    print(f"    Task Type: {plan.get('task_type', 'unknown')}")
    print(f"    Steps: {plan.get('total_steps', 0)}")
    for step in plan.get("steps", []):
        print(f"      Step {step['step']}: [{step['agent']}] {step['action']} — {step['status']}")

async def cmd_aigos_leaderboard():
    """Show benchmark leaderboard."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    leaderboard = ai.aigos_benchmark_leaderboard()
    print(f"\n  Benchmark Leaderboard ({len(leaderboard)} providers):")
    if not leaderboard:
        print("    No benchmarks yet. Run 'aigos benchmark' first.")
    for entry in leaderboard:
        print(f"    #{entry['rank']} {entry['provider']:20s}  score={entry['score']:.2f}  benchmarks={entry['benchmarks']}")

async def cmd_aigos_knowledge(query, domain=""):
    """Search the AIG-OS knowledge base."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = ai.aigos_knowledge_query(query, domain)
    total = result.get("total_matches", 0)
    print(f"\n  Knowledge Search: '{query}' — {total} matches")
    for dom, entries in result.get("results", {}).items():
        print(f"    [{dom}]")
        for key in list(entries.keys())[:5]:
            print(f"      {key}")

async def cmd_aigos_providers():
    """List researched providers."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    providers = ai.aigos_providers()
    print(f"\n  Researched Providers ({len(providers)}):")
    for p in providers:
        free = "FREE" if p.get("free_tier") else "PAID"
        print(f"    {p['name']:25s}  type={p.get('type', 'unknown'):20s}  {free}")

async def cmd_aigos_endpoints():
    """List discovered endpoints."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    endpoints = ai.aigos_endpoints()
    print(f"\n  Discovered Endpoints ({len(endpoints)}):")
    for e in endpoints:
        auth = e.get("auth", "unknown")
        print(f"    {e['name']:25s}  type={e.get('type', 'unknown'):20s}  auth={auth}")


# ── Phase 33-36 — Quality Engineering Commands ────────────────

async def cmd_quality_gates(file_path=""):
    """Run all quality gates on a file."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    code = ""
    if file_path and Path(file_path).exists():
        with open(file_path) as f:
            code = f.read()
    gates = await ai.quality_gates.run_all_gates(file_path or "<input>", code)
    print(f"\n  Quality Gates (Swiss Cheese Model)\n")
    for result in gates:
        icon = "✅" if result.result.value == "passed" else "❌"
        print(f"    {icon} {result.gate_name:20s}  {result.message[:60]}")


async def cmd_review_code(file_path=""):
    """Run multi-agent code review on a file."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    code = ""
    if file_path and Path(file_path).exists():
        with open(file_path) as f:
            code = f.read()
    review = ai.multi_agent_review.simulate_review(code, file_path or "<input>")
    print(f"\n  Multi-Agent Code Review\n")
    print(f"    Quality Score: {review.quality_score:.0f}/100")
    print(f"    Total Findings: {review.total_findings}")
    for severity, count in review.by_severity.items():
        if count:
            print(f"    {severity}: {count}")
    print(f"\n    Summary: {review.summary}")


async def cmd_scan_secrets(file_path=""):
    """Scan a file for secrets."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    code = ""
    if file_path and Path(file_path).exists():
        with open(file_path) as f:
            code = f.read()
    findings = ai.secret_scanner.scan_text(code, file_path or "<input>")
    print(f"\n  Secret Scanner\n")
    if not findings:
        print("    ✅ No secrets found")
    for finding in findings:
        print(f"    ❌ {finding.pattern_name:30s} line={finding.line}  confidence={finding.confidence:.0%}")


async def cmd_analyze_code(file_path=""):
    """Run static and structural analysis on a file."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    code = ""
    if file_path and Path(file_path).exists():
        with open(file_path) as f:
            code = f.read()
    static = ai.static_analyzer.analyze_code(code, file_path or "<input>")
    structural = ai.structural_analyzer.analyze({file_path or "<input>": code})
    print(f"\n  Code Analysis\n")
    print(f"    Static Issues: {len(static)}")
    for issue in static[:10]:
        print(f"      [{issue.severity}] {issue.rule_id} {issue.message[:60]}")
    print(f"\n    Structural Findings: {len(structural)}")
    for finding in structural[:10]:
        print(f"      [{finding.severity}] {finding.category} {finding.message[:60]}")


async def cmd_debt_scan(file_path=""):
    """Scan a file for technical debt."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    code = ""
    if file_path and Path(file_path).exists():
        with open(file_path) as f:
            code = f.read()
    items = ai.debt_tracker.scan_codebase({file_path or "<input>": code})
    print(f"\n  Technical Debt Scan\n")
    if not items:
        print("    ✅ No debt items found")
    for item in items[:15]:
        print(f"    [{item.priority}] {item.category:15s} line={item.line}  {item.description[:60]}")


async def cmd_refactor_suggest(file_path=""):
    """Suggest refactorings for a file."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    code = ""
    if file_path and Path(file_path).exists():
        with open(file_path) as f:
            code = f.read()
    suggestions = ai.refactoring_engine.analyze(code, file_path or "<input>")
    print(f"\n  Refactoring Suggestions\n")
    if not suggestions:
        print("    ✅ No refactoring needed")
    for s in suggestions[:10]:
        print(f"    [{s.effort}] {s.technique:35s} {s.smell.description[:50]}")


async def cmd_quality_report(file_path=""):
    """Run the comprehensive quality dashboard on a file."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    code = ""
    if file_path and Path(file_path).exists():
        with open(file_path) as f:
            code = f.read()
    report = ai.quality_dashboard.analyze(code, file_path or "<input>")
    print(f"\n  Quality Dashboard\n")
    print(f"    Overall: {report.overall_grade} ({report.overall_score:.0f}/100)")
    print(f"    Summary: {report.summary}\n")
    for dim in report.dimensions:
        print(f"    {dim['name']:20s} {dim['grade']:3s} {dim['score']:.0f}/100  findings={dim['findings_count']}")
    if report.recommendations:
        print(f"\n  Recommendations:")
        for rec in report.recommendations:
            print(f"    → {rec}")


async def cmd_orchestrate(file_path=""):
    """Run the orchestration pipeline on a file."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    code = ""
    if file_path and Path(file_path).exists():
        with open(file_path) as f:
            code = f.read()
    result = ai.orchestration_pipeline.run_full_pipeline(code, file_path or "<input>")
    print(f"\n  Orchestration Pipeline\n")
    for stage in result["stages"]:
        icon = "✅" if stage["result"] == "pass" else ("❌" if stage["result"] == "fail" else "⚠️")
        print(f"    {icon} {stage['stage']:15s} {stage['summary'][:60]}")
    print(f"\n    Final Result: {result['final_result']}")
    print(f"    Total Findings: {result['total_findings']}")


# ── Research Integration Commands ───────────────────────────────

async def cmd_research_index():
    """Show the research <-> implementation integration index."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    index = ai.research_integration.build_index()
    print(f"\n  Research Integration Index\n")
    print(f"  Research Documents: {index['research_documents']}")
    print(f"  Capabilities:       {index['capabilities']}")
    print(f"  Modules:            {len(index['modules'])}")
    linked = sum(1 for v in index["capability_links"].values() if v.get("modules"))
    print(f"  Capabilities Linked: {linked}")


async def cmd_research_trace(capability_id):
    """Trace a capability to its research source and implementation."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    trace = ai.trace_capability(capability_id)
    if trace is None:
        print(f"\n  Capability {capability_id} not found")
        return
    print(f"\n  Traceability: {trace.capability_id} — {trace.name} [{trace.status}]")
    print(f"  Research:    {', '.join(r['research_id'] for r in trace.research_documents) or 'none'}")
    print(f"  Modules:     {', '.join(trace.modules) or 'none'}")
    print(f"  Tests:       {', '.join(trace.tests) or 'none'}")
    print(f"  SDK:         {', '.join(trace.sdk_interfaces) or 'none'}")
    print(f"  MCP:         {', '.join(trace.mcp_tools) or 'none'}")
    print(f"  Benchmarks:  {', '.join(trace.benchmarks) or 'none'}")
    print(f"  Introduced:  {trace.introduced_commit or 'unknown'}")
    print(f"  Vault:       {trace.vault_page}")


async def cmd_research_impact(research_id):
    """Show the implementation blast radius of a research document."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    impact = ai.research_impact(research_id)
    if impact is None:
        print(f"\n  Research document {research_id} not found")
        return
    print(f"\n  Impact Analysis: {impact.research_id} — {impact.title}")
    print(f"  Capabilities: {len(impact.affected_capabilities)}")
    print(f"  Modules:      {', '.join(impact.affected_modules) or 'none'}")
    print(f"  Tests:        {', '.join(impact.affected_tests) or 'none'}")
    print(f"  SDK:          {', '.join(impact.affected_sdk_interfaces) or 'none'}")
    print(f"  MCP Tools:    {', '.join(impact.affected_mcp_tools) or 'none'}")
    print(f"\n  Recommendations:")
    for rec in impact.recommendations:
        print(f"    → {rec}")


async def cmd_research_sync():
    """Detect research changes and refresh the index."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    report = ai.research_integration.sync()
    print(f"\n  Research Sync\n")
    print(f"  Documents Indexed: {report['documents_indexed']}")
    print(f"  Changes Detected: {len(report['changes'])}")
    for change in report["changes"][:10]:
        print(f"    [{change['type']}] {change['research_id']} — {change.get('title', '')}")
    if report["queue_added"]:
        print(f"\n  Queue Additions:")
        for item in report["queue_added"]:
            print(f"    [{item['classification']}] {item['topic']} ({item['reason']})")


async def cmd_research_graph():
    """Show the traversable research <-> implementation graph."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    graph = ai.research_graph()
    print(f"\n  Research Implementation Graph\n")
    print(f"  Nodes: {graph['node_count']}  Edges: {graph['edge_count']}")
    by_type = {}
    for node in graph["nodes"]:
        by_type[node["type"]] = by_type.get(node["type"], 0) + 1
    for t, count in sorted(by_type.items()):
        print(f"    {t:12s} {count}")


# ── Kimi K3 Commands ──

async def cmd_kimi_chat(prompt, provider="auto", system_prompt="", reasoning_effort="max",
                     max_tokens=0, strategy="auto"):
    """Chat with Kimi K3 through the best available execution path."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.chat(
        prompt, provider=provider, system_prompt=system_prompt,
        reasoning_effort=reasoning_effort,
        max_tokens=int(max_tokens) if max_tokens else None,
        strategy=strategy,
    )
    print(f"\n  Provider:    {result.get('provider', '')}")
    print(f"  Model:       {result.get('model', 'kimi-k3')}")
    print(f"  Latency:     {result.get('latency_ms', 0)}ms")
    print(f"  Quality:     {result.get('quality_score', 0)}")
    if result.get("reasoning"):
        print(f"  Reasoning:   {result['reasoning'][:300]}")
    print(f"  Answer:      {result.get('text', '')}")
    if result.get("error"):
        print(f"  Error:       {result['error']}")
    return result


async def cmd_kimi_info():
    """Print the canonical Kimi K3 specification and supported paths."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    info = ai.kimi_k3_info()
    spec = info["spec"]
    print(f"\n  Kimi K3 — {spec['model']} ({spec['model_id']})")
    print(f"  Architecture: {spec['architecture']['family']} — {spec['architecture']['total_params']} total / {spec['architecture']['active_params']} active")
    print(f"  Context:      {spec['context_length']:,} tokens")
    print(f"  Multimodal:   {spec['architecture']['multimodal']} (MoonViT-V2)")
    print(f"  Weights:      {spec['architecture']['weights_dtype']} / activations {spec['architecture']['activations_dtype']}")
    print(f"  License:      {spec['license']['name']}")
    print(f"\n  Supported paths:")
    for path in info["supported_paths"]:
        print(f"    OK {path['name']}: {path['description']}")
    print(f"\n  Unsupported paths (officially):")
    for path in info["unsupported_paths"]:
        print(f"    NO {path['name']}: {path['reason']}")


async def cmd_kimi_health():
    """Health-check every configured Kimi K3 execution path."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    health = await ai.kimi_k3_health()
    print("\n  Kimi K3 endpoint health:")
    for name, h in health.items():
        status = "OK" if h.get("healthy") else "FAIL"
        print(f"    {name:18s} {status}  {h.get('url', '')}")
        if h.get("models"):
            print(f"      models: {', '.join(h['models'][:5])}")
        if h.get("error"):
            print(f"      error:  {h['error']}")
    return health


async def cmd_kimi_benchmark(prompt="Explain Mixture of Experts.", runs=2,
                             provider="auto", reasoning_effort="low"):
    """Benchmark Kimi K3 chat latency and quality."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    result = await ai.kimi_k3_benchmark(
        prompt, runs=runs, provider=provider, reasoning_effort=reasoning_effort,
    )
    print("\n  Kimi K3 benchmark:")
    for i, r in enumerate(result.get("runs", []), 1):
        status = "OK" if r.get("success") else "FAIL"
        print(f"    run {i}: {status}  {r.get('provider', '')}  "
              f"{r.get('latency_ms', 0)}ms  quality {r.get('quality_score', 0)}")
    print(f"    summary: {result.get('stats', {})}")
    return result


async def cmd_tools(category="", status="", search=""):
    """List code-quality tools from the unified registry."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    tools = ai.list_tools(category=category, status=status, search=search)
    stats = ai.get_tool_registry_stats()
    print(f"\n  Tool Registry — {len(tools)} shown / {stats['total_tools']} total"
          f" ({stats['ready']} ready, {stats['blocked']} blocked)")
    print(f"  {'ID':<16s} {'STATUS':<8s} {'VERIFIED':<9s} {'CATEGORY':<14s} PACKAGE")
    for t in tools:
        verified = "yes" if t.get("verified") else "no"
        print(f"  {t['id']:<16s} {t.get('status','ready'):<8s} {verified:<9s} "
              f"{t.get('category','-'):<14s} {t.get('package','-') or '-'}")
        if t.get("note"):
            print(f"    {t['note'][:110]}")
    return {"tools": tools, "stats": stats}


async def cmd_mcp_check(server_id="", live=False):
    """Validate one MCP server (offline config) or live probe it (--live)."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    print("")
    if not live:
        result = ai.validate_mcp_server(server_id)
        print(f"  MCP config validation — {server_id}: {result['status']}")
        for err in result.get("errors", []):
            print(f"    - {err}")
        return result
    result = ai.check_mcp_server_health(server_id, timeout=8.0)
    print(f"  MCP live probe — {server_id}: {result['status']}")
    if result.get("note"):
        print(f"    {result['note']}")
    if result.get("stderr_tail"):
        print(f"    stderr: {result['stderr_tail'][-200:]}")
    return result


async def cmd_mcp_check_all(live=False):
    """Validate all servers: offline config checks, or live probes with --live."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    print("")
    if live:
        print("  Running live probes across all servers (network required)...")
    results = ai.run_mcp_validation(live=live)
    ok = sum(1 for r in results if r.get("valid", r.get("healthy", False)))
    print(f"  MCP validation — {len(results)} servers, {ok} ok"
          f"{' (live probes)' if live else ''}")
    for r in results:
        flag = "OK " if r.get("valid", r.get("healthy", False)) else "FAIL"
        print(f"  [{flag}] {r['server_id']}: {r.get('status')}")
        for err in r.get("errors", []):
            print(f"         - {err}")
    return results



    """Validate one MCP server (offline config) or all (live probes with --all)."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    print("")
    if server_id and not live:
        result = ai.validate_mcp_server(server_id)
        print(f"  MCP config validation — {server_id}: {result['status']}")
        for err in result.get("errors", []):
            print(f"    - {err}")
        return result
    if server_id and live:
        result = ai.check_mcp_server_health(server_id, timeout=8.0)
        print(f"  MCP live probe — {server_id}: {result['status']}")
        if result.get("note"):
            print(f"    {result['note']}")
        if result.get("stderr_tail"):
            print(f"    stderr: {result['stderr_tail'][-200:]}")
        return result
    results = ai.run_mcp_validation(live=live)
    ok = sum(1 for r in results if r.get("valid", r.get("healthy", False)))
    print(f"  MCP validation — {len(results)} servers, {ok} ok")
    for r in results:
        flag = "OK " if r.get("valid", r.get("healthy", False)) else "FAIL"
        print(f"  [{flag}] {r['server_id']}: {r.get('status')}")
        for err in r.get("errors", []):
            print(f"         - {err}")
    return results


async def cmd_skills(category="", status="", search=""):
    """List skills from the unified registry."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    skills = ai.list_skills(category=category, status=status, search=search)
    stats = ai.get_skill_registry_stats()
    print(f"\n  Skill Registry — {len(skills)} shown / {stats['total_skills']} total"
          f" ({stats['ready']} ready, {stats['blocked']} blocked,"
          f" {stats['verified']} verified)")
    print(f"  {'ID':<28s} {'STATUS':<8s} {'VERIFIED':<9s} {'CATEGORY':<22s} SOURCE")
    for sk in skills:
        verified = "yes" if sk.get("verified") else "no"
        print(f"  {sk['id']:<28s} {sk.get('status','ready'):<8s} {verified:<9s} "
              f"{sk.get('category','-'):<22s} {sk.get('source','-')}")
        if sk.get("note"):
            print(f"    {sk['note'][:110]}")
    return {"skills": skills, "stats": stats}


async def cmd_mcp_servers(category="", status="", search=""):
    """List MCP servers from the unified registry."""
    from ai_generation.sdk import UncleFrappeAI
    ai = UncleFrappeAI()
    servers = ai.list_mcp_servers(category=category, status=status, search=search)
    stats = ai.get_mcp_registry_stats()
    print(f"\n  MCP Server Registry — {len(servers)} shown / {stats['total_servers']} total"
          f" ({stats['ready']} ready, {stats['blocked']} blocked)")
    print(f"  {'ID':<18s} {'STATUS':<8s} {'VERIFIED':<9s} {'PACKAGE'}")
    for s in servers:
        verified = "yes" if s.get("verified") else "no"
        print(f"  {s['id']:<18s} {s.get('status','ready'):<8s} {verified:<9s} "
              f"{s.get('package','-') or '-'}")
        if s.get("note"):
            print(f"    {s['note'][:110]}")
    return {"servers": servers, "stats": stats}
    print(f"\n  Configured endpoints:")
    for ep in info["configured_endpoints"]:
        key = "key set" if ep["api_key_set"] else "no key"
        print(f"    - {ep['name']:20s} {ep['url']:50s} {key}")
    return info


async def main():
    """Dispatch CLI subcommands to their handlers."""
    args = sys.argv[1:]
    if not args or args[0] == "--help":
        print("""
  Uncle Frappe AI — Generation CLI

  Usage:
    python -m ai_generation.cli generate <prompt> [--style STYLE] [--width W] [--height H] [--provider NAME]
    python -m ai_generation.cli text <prompt> [--model MODEL] [--system SYSTEM]
    python -m ai_generation.cli embed <text>             Local 384-dim embedding (sentence-transformers)
    python -m ai_generation.cli translate <text> [--target fr]  Local translation (Helsinki-NLP opus-mt)
    python -m ai_generation.cli tts <text> [--output FILE]       Local TTS (Piper, no API key)
    python -m ai_generation.cli stt <audio_file>        Local STT (faster-whisper)
    python -m ai_generation.cli ocr <image_file>        OCR with Tesseract
    python -m ai_generation.cli upscale <image_file> [--output FILE]  Real-ESRGAN 4x upscale
    python -m ai_generation.cli bg-remove <image_file> [--output FILE]  rembg background removal
    python -m ai_generation.cli local-backends          List free local backends
    python -m ai_generation.cli storage-list            List storage backends
    python -m ai_generation.cli storage-write <col> <key> <value> [--task T]  Write a record
    python -m ai_generation.cli storage-read <col> <key> [--task T]  Read a record
    python -m ai_generation.cli storage-query <col> [--limit N] [--task T]  Query records
    python -m ai_generation.cli storage-stats           Storage statistics
    python -m ai_generation.cli event-classes          Event taxonomy + delivery guarantees
    python -m ai_generation.cli event-emit <subject> <payload>  Emit durable event
    python -m ai_generation.cli event-replay [subject] Replay durable events
    python -m ai_generation.cli event-stats           Durable event log statistics
    python -m ai_generation.cli event-purge [status]  Purge events (default dead_letter)
    python -m ai_generation.cli cap-graph-sync        Sync capability graph from registries
    python -m ai_generation.cli compat                 Compatibility matrix stats
    python -m ai_generation.cli compat-lookup <model> <runtime> [hardware]  Lookup combination
    python -m ai_generation.cli compat-runtimes <model> [hardware]  Best runtimes for model
    python -m ai_generation.cli compat-models <category> [hardware]  Best models for category
    python -m ai_generation.cli compat-validate <model> <runtime> [hardware]  Validate path
    python -m ai_generation.cli video <prompt> [--duration SECS] [--width W] [--height H]
    python -m ai_generation.cli enhance <prompt> [--style STYLE]
    python -m ai_generation.cli providers               List available providers
    python -m ai_generation.cli benchmarks [prompt]      Run provider benchmarks
    python -m ai_generation.cli known                    List known providers from research
    python -m ai_generation.cli stats                    Platform statistics

    Phase 11 — Media Intelligence & Cinematic Production:
    python -m ai_generation.cli analyze <prompt>         Analyze request & recommend strategy
    python -m ai_generation.cli edit <op> <file> [prompt]  Image editing operations
    python -m ai_generation.cli video-gen <prompt>       True AI video generation
    python -m ai_generation.cli plan <request>           Plan complete media production
    python -m ai_generation.cli character [create|list|prompt]  Character management
    python -m ai_generation.cli project [create|list]    Project management
    python -m ai_generation.cli cinema-dims              Cinema benchmark dimensions
    python -m ai_generation.cli capabilities             Capability matrix
    python -m ai_generation.cli intel                    Provider intelligence
    python -m ai_generation.cli video-caps               Video generation capabilities

    Phase 33-36 — Quality Engineering:
    python -m ai_generation.cli quality-gates [file]   Run all quality gates
    python -m ai_generation.cli review [file]          Multi-agent code review
    python -m ai_generation.cli scan-secrets [file]    Scan for secrets
    python -m ai_generation.cli analyze-code [file]    Static + structural analysis
    python -m ai_generation.cli debt-scan [file]       Scan for technical debt
    python -m ai_generation.cli refactor [file]        Refactoring suggestions
    python -m ai_generation.cli quality-report [file]  Quality dashboard
    python -m ai_generation.cli orchestrate [file]     Orchestration pipeline

    Research Integration:
    python -m ai_generation.cli research-index       Research integration index
    python -m ai_generation.cli research-trace ID    Trace a capability
    python -m ai_generation.cli research-impact ID   Research impact analysis
    python -m ai_generation.cli research-sync        Detect and sync research
    python -m ai_generation.cli research-graph       Implementation graph

    Phase 14 — AIG-OS Autonomous Agents:
    aigos-status             Show AIG-OS orchestrator status
    aigos-agents             List all autonomous agents
    aigos-execute <req>      Execute through AIG-OS pipeline
    aigos-leaderboard        Show benchmark leaderboard
    aigos-knowledge <query>  Search knowledge base
    aigos-providers          List researched providers
    aigos-endpoints          List discovered endpoints

  Phase 13 — Agent-Native Remote Execution:
    python -m ai_generation.cli agent-generate <request>  Agent-native generation
    python -m ai_generation.cli endpoints                 List all execution endpoints
    python -m ai_generation.cli health-check              Check provider health
    python -m ai_generation.cli cap-matrix                Capability registry
    python -m ai_generation.cli discover                  Provider discovery
    python -m ai_generation.cli provider-rank [TYPE]   Refresh + rank provider network
    python -m ai_generation.cli health-cycle           Run persisted provider health cycle
    python -m ai_generation.cli add-endpoint <name> <url> Add remote endpoint
    python -m ai_generation.cli classify <request>        Classify a request

  Styles: photorealistic, cinematic, anime, digital_art, oil_painting, watercolor,
          3d_render, minimalist, product_photo, food_photo, architectural, portrait
""")
    elif args[0] == "generate":
        prompt = args[1] if len(args) > 1 else "a beautiful sunset"
        style = ""
        width, height, provider = 1024, 1024, ""
        i = 2
        while i < len(args):
            if args[i] == "--style" and i + 1 < len(args):
                style = args[i + 1]; i += 2
            elif args[i] == "--width" and i + 1 < len(args):
                width = int(args[i + 1]); i += 2
            elif args[i] == "--height" and i + 1 < len(args):
                height = int(args[i + 1]); i += 2
            elif args[i] == "--provider" and i + 1 < len(args):
                provider = args[i + 1]; i += 2
            else:
                i += 1
        await cmd_generate(prompt, style=style, width=width, height=height, provider=provider)
    elif args[0] == "text":
        prompt = args[1] if len(args) > 1 else "Explain the unified AI generation platform in one sentence."
        model, system_prompt = "", ""
        i = 2
        while i < len(args):
            if args[i] == "--model" and i + 1 < len(args):
                model = args[i + 1]; i += 2
            elif args[i] == "--system" and i + 1 < len(args):
                system_prompt = args[i + 1]; i += 2
            else:
                i += 1
        await cmd_text(prompt, model=model, system_prompt=system_prompt)
    elif args[0] == "embed":
        text = args[1] if len(args) > 1 else "The unified AI generation platform."
        await cmd_embed(text)
    elif args[0] == "translate":
        text = args[1] if len(args) > 1 else "Hello, how are you today?"
        target_lang, source_lang = "fr", ""
        i = 2
        while i < len(args):
            if args[i] == "--target" and i + 1 < len(args):
                target_lang = args[i + 1]; i += 2
            elif args[i] == "--source" and i + 1 < len(args):
                source_lang = args[i + 1]; i += 2
            else:
                i += 1
        await cmd_translate(text, target_lang=target_lang, source_lang=source_lang)
    elif args[0] == "tts":
        text = args[1] if len(args) > 1 else "Hello from the unified AI generation platform."
        output = ""
        i = 2
        while i < len(args):
            if args[i] == "--output" and i + 1 < len(args):
                output = args[i + 1]; i += 2
            else:
                i += 1
        await cmd_tts(text, output_path=output)
    elif args[0] == "stt":
        if len(args) < 2:
            print("  Usage: stt <audio_file> [--model tiny|base|small]")
        else:
            model = ""
            if "--model" in args:
                idx = args.index("--model")
                if idx + 1 < len(args):
                    model = args[idx + 1]
            await cmd_stt(args[1], model=model)
    elif args[0] == "ocr":
        if len(args) < 2:
            print("  Usage: ocr <image_file>")
        else:
            await cmd_ocr(args[1])
    elif args[0] == "upscale":
        if len(args) < 2:
            print("  Usage: upscale <image_file> [--output FILE]")
        else:
            output = ""
            if "--output" in args:
                idx = args.index("--output")
                if idx + 1 < len(args):
                    output = args[idx + 1]
            await cmd_upscale(args[1], output_path=output)
    elif args[0] == "bg-remove":
        if len(args) < 2:
            print("  Usage: bg-remove <image_file> [--output FILE]")
        else:
            output = ""
            if "--output" in args:
                idx = args.index("--output")
                if idx + 1 < len(args):
                    output = args[idx + 1]
            await cmd_bg_remove(args[1], output_path=output)
    elif args[0] == "local-backends":
        await cmd_local_backends()
    elif args[0] == "storage-list":
        await cmd_storage_list()
    elif args[0] == "storage-write":
        if len(args) < 4:
            print("  Usage: storage-write <collection> <key> <value> [--task metadata|ledger|audit|embeddings|artifacts|graph|metrics|cache]")
        else:
            task = "metadata"
            if "--task" in args:
                idx = args.index("--task")
                if idx + 1 < len(args):
                    task = args[idx + 1]
            await cmd_storage_write(args[1], args[2], args[3], task=task)
    elif args[0] == "storage-read":
        if len(args) < 3:
            print("  Usage: storage-read <collection> <key> [--task T]")
        else:
            task = "metadata"
            if "--task" in args:
                idx = args.index("--task")
                if idx + 1 < len(args):
                    task = args[idx + 1]
            await cmd_storage_read(args[1], args[2], task=task)
    elif args[0] == "storage-query":
        if len(args) < 2:
            print("  Usage: storage-query <collection> [--limit N] [--task T]")
        else:
            limit, task = 100, "metadata"
            i = 2
            while i < len(args):
                if args[i] == "--limit" and i + 1 < len(args):
                    limit = int(args[i + 1]); i += 2
                elif args[i] == "--task" and i + 1 < len(args):
                    task = args[i + 1]; i += 2
                else:
                    i += 1
            await cmd_storage_query(args[1], limit=limit, task=task)
    elif args[0] == "storage-stats":
        await cmd_storage_stats()
    elif args[0] == "event-classes":
        await cmd_event_classes()
    elif args[0] == "event-emit":
        if len(args) < 3:
            print("  Usage: event-emit <subject> <payload>")
        else:
            await cmd_event_emit(args[1], args[2])
    elif args[0] == "event-replay":
        subject = args[1] if len(args) > 1 else ""
        await cmd_event_replay(subject)
    elif args[0] == "event-stats":
        await cmd_event_stats()
    elif args[0] == "event-purge":
        status = args[1] if len(args) > 1 else "dead_letter"
        await cmd_event_purge(status)
    elif args[0] == "cap-graph-sync":
        await cmd_graph_sync()
    elif args[0] == "compat":
        await cmd_compat_stats()
    elif args[0] == "compat-lookup":
        model = args[1] if len(args) > 1 else ""
        runtime = args[2] if len(args) > 2 else ""
        hardware = args[3] if len(args) > 3 else "all"
        await cmd_compat_lookup(model, runtime, hardware)
    elif args[0] == "compat-runtimes":
        model = args[1] if len(args) > 1 else ""
        hardware = args[2] if len(args) > 2 else ""
        await cmd_compat_runtimes(model, hardware)
    elif args[0] == "compat-models":
        category = args[1] if len(args) > 1 else ""
        hardware = args[2] if len(args) > 2 else ""
        await cmd_compat_models(category, hardware)
    elif args[0] == "compat-validate":
        model = args[1] if len(args) > 1 else ""
        runtime = args[2] if len(args) > 2 else ""
        hardware = args[3] if len(args) > 3 else "all"
        await cmd_compat_validate(model, runtime, hardware)
    elif args[0] == "video":
        prompt = args[1] if len(args) > 1 else "a timelapse of clouds"
        duration, width, height = 4.0, 1280, 720
        i = 2
        while i < len(args):
            if args[i] == "--duration" and i + 1 < len(args):
                duration = float(args[i + 1]); i += 2
            elif args[i] == "--width" and i + 1 < len(args):
                width = int(args[i + 1]); i += 2
            elif args[i] == "--height" and i + 1 < len(args):
                height = int(args[i + 1]); i += 2
            else:
                i += 1
        await cmd_video(prompt, duration=duration, width=width, height=height)
    elif args[0] == "enhance":
        prompt = args[1] if len(args) > 1 else "a coffee cup"
        style = "photorealistic"
        if "--style" in args:
            idx = args.index("--style")
            if idx + 1 < len(args):
                style = args[idx + 1]
        await cmd_enhance(prompt, style=style)
    elif args[0] == "providers":
        await cmd_providers()
    elif args[0] == "benchmarks":
        prompt = args[1] if len(args) > 1 else "a beautiful landscape"
        await cmd_benchmarks(prompt)
    elif args[0] == "known":
        await cmd_providers_list()
    elif args[0] == "stats":
        await cmd_stats()
    elif args[0] == "analyze":
        prompt = args[1] if len(args) > 1 else "a luxury cafe advertisement"
        await cmd_analyze(prompt)
    elif args[0] == "edit":
        if len(args) < 3:
            print("  Usage: edit <operation> <input_path> [prompt] [mask_path]")
            print("  Operations: img2img, inpaint, outpaint, remove_bg, replace_bg, style_transfer, upscale")
        else:
            op_map = {
                "img2img": "img2img", "inpaint": "inpainting", "outpaint": "outpainting",
                "remove_bg": "background_removal", "replace_bg": "background_replacement",
                "style_transfer": "style_transfer", "upscale": "upscale",
            }
            op = op_map.get(args[1], args[1])
            await cmd_edit(op, args[2], prompt=args[3] if len(args) > 3 else "", mask=args[4] if len(args) > 4 else "")
    elif args[0] == "video-gen":
        prompt = args[1] if len(args) > 1 else "a cinematic scene"
        image = ""
        duration = 4.0
        i = 2
        while i < len(args):
            if args[i] == "--image" and i + 1 < len(args):
                image = args[i + 1]; i += 2
            elif args[i] == "--duration" and i + 1 < len(args):
                duration = float(args[i + 1]); i += 2
            else:
                i += 1
        await cmd_video_gen(prompt, duration=duration, image_path=image)
    elif args[0] == "plan":
        request = args[1] if len(args) > 1 else "Create a luxury cafe advertisement"
        await cmd_plan(request)
    elif args[0] == "character":
        action = args[1] if len(args) > 1 else "list"
        name = args[2] if len(args) > 2 else ""
        char_id = args[2] if len(args) > 2 else ""
        await cmd_character(action, name=name, char_id=char_id)
    elif args[0] == "project":
        action = args[1] if len(args) > 1 else "list"
        name = args[2] if len(args) > 2 else ""
        await cmd_project(action, name=name)
    elif args[0] == "cinema-dims":
        await cmd_cinema_dims()
    elif args[0] == "capabilities":
        await cmd_capabilities()
    elif args[0] == "intel":
        await cmd_intel()
    elif args[0] == "video-caps":
        await cmd_video_caps()
    elif args[0] == "agent-generate":
        request = args[1] if len(args) > 1 else "a beautiful sunset"
        await cmd_agent_generate(request)
    elif args[0] == "endpoints":
        await cmd_endpoints()
    elif args[0] == "health-check":
        await cmd_health()
    elif args[0] == "cap-matrix":
        await cmd_cap_matrix()
    elif args[0] == "health-cycle":
        await cmd_health_cycle()
    elif args[0] == "provider-rank":
        provider_type = args[1] if len(args) > 1 else ""
        await cmd_provider_rank(provider_type)
    elif args[0] == "discover":
        await cmd_discover()
    elif args[0] == "add-endpoint":
        if len(args) < 3:
            print("  Usage: add-endpoint <name> <url>")
        else:
            await cmd_add_endpoint(args[1], args[2])
    elif args[0] == "classify":
        request = args[1] if len(args) > 1 else "generate a luxury cafe advertisement"
        await cmd_classify(request)

    # Phase 33-36 — Quality Engineering
    elif args[0] == "quality-gates":
        await cmd_quality_gates(args[1] if len(args) > 1 else "")
    elif args[0] == "review":
        await cmd_review_code(args[1] if len(args) > 1 else "")
    elif args[0] == "scan-secrets":
        await cmd_scan_secrets(args[1] if len(args) > 1 else "")
    elif args[0] == "analyze-code":
        await cmd_analyze_code(args[1] if len(args) > 1 else "")
    elif args[0] == "debt-scan":
        await cmd_debt_scan(args[1] if len(args) > 1 else "")
    elif args[0] == "refactor":
        await cmd_refactor_suggest(args[1] if len(args) > 1 else "")
    elif args[0] == "quality-report":
        await cmd_quality_report(args[1] if len(args) > 1 else "")
    elif args[0] == "orchestrate":
        await cmd_orchestrate(args[1] if len(args) > 1 else "")
    elif args[0] == "research-index":
        await cmd_research_index()
    elif args[0] == "research-trace":
        await cmd_research_trace(args[1] if len(args) > 1 else "IMG-01")
    elif args[0] == "research-impact":
        await cmd_research_impact(args[1] if len(args) > 1 else "SECURITY_CANON")
    elif args[0] == "research-sync":
        await cmd_research_sync()
    elif args[0] == "research-graph":
        await cmd_research_graph()
    elif args[0] == "kimi-chat":
        prompt = args[1] if len(args) > 1 else "Explain what you are."
        provider = "auto"
        reasoning_effort = "max"
        system_prompt = ""
        max_tokens = 0
        strategy = "auto"
        i = 2
        while i < len(args):
            if args[i] == "--provider" and i + 1 < len(args):
                provider = args[i + 1]; i += 2
            elif args[i] == "--effort" and i + 1 < len(args):
                reasoning_effort = args[i + 1]; i += 2
            elif args[i] == "--system" and i + 1 < len(args):
                system_prompt = args[i + 1]; i += 2
            elif args[i] == "--max-tokens" and i + 1 < len(args):
                max_tokens = int(args[i + 1]); i += 2
            elif args[i] == "--strategy" and i + 1 < len(args):
                strategy = args[i + 1]; i += 2
            else:
                i += 1
        await cmd_kimi_chat(prompt, provider=provider, system_prompt=system_prompt,
                            reasoning_effort=reasoning_effort, max_tokens=max_tokens,
                            strategy=strategy)
    elif args[0] == "kimi-info":
        await cmd_kimi_info()
    elif args[0] == "kimi-health":
        await cmd_kimi_health()
    elif args[0] == "tools":
        category = ""
        status = ""
        search = ""
        i = 1
        while i < len(args):
            if args[i] == "--category" and i + 1 < len(args):
                category = args[i + 1]; i += 2
            elif args[i] == "--status" and i + 1 < len(args):
                status = args[i + 1]; i += 2
            elif args[i] == "--search" and i + 1 < len(args):
                search = args[i + 1]; i += 2
            else:
                i += 1
        await cmd_tools(category=category, status=status, search=search)
    elif args[0] == "mcp-check":
        server_id = ""
        live = False
        all_servers = False
        i = 1
        while i < len(args):
            if args[i] == "--all":
                all_servers = True
            elif args[i] == "--live":
                live = True
            elif not args[i].startswith("-"):
                server_id = args[i]
            i += 1
        if all_servers and not server_id:
            results = await cmd_mcp_check_all(live=live)
        else:
            await cmd_mcp_check(server_id=server_id, live=live)
    elif args[0] == "skills":
        category = ""
        status = ""
        search = ""
        i = 1
        while i < len(args):
            if args[i] == "--category" and i + 1 < len(args):
                category = args[i + 1]; i += 2
            elif args[i] == "--status" and i + 1 < len(args):
                status = args[i + 1]; i += 2
            elif args[i] == "--search" and i + 1 < len(args):
                search = args[i + 1]; i += 2
            else:
                i += 1
        await cmd_skills(category=category, status=status, search=search)
    elif args[0] == "mcp-servers":
        category = ""
        status = ""
        search = ""
        i = 1
        while i < len(args):
            if args[i] == "--category" and i + 1 < len(args):
                category = args[i + 1]; i += 2
            elif args[i] == "--status" and i + 1 < len(args):
                status = args[i + 1]; i += 2
            elif args[i] == "--search" and i + 1 < len(args):
                search = args[i + 1]; i += 2
            else:
                i += 1
        await cmd_mcp_servers(category=category, status=status, search=search)
    elif args[0] == "kimi-benchmark":
        prompt = args[1] if len(args) > 1 else "Explain Mixture of Experts."
        runs = 2
        provider = "auto"
        effort = "low"
        i = 2
        while i < len(args):
            if args[i] == "--runs" and i + 1 < len(args):
                runs = int(args[i + 1]); i += 2
            elif args[i] == "--provider" and i + 1 < len(args):
                provider = args[i + 1]; i += 2
            elif args[i] == "--effort" and i + 1 < len(args):
                effort = args[i + 1]; i += 2
            else:
                i += 1
        await cmd_kimi_benchmark(prompt, runs=runs, provider=provider,
                                 reasoning_effort=effort)


if __name__ == "__main__":
    asyncio.run(main())
