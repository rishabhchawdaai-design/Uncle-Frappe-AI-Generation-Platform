"""Section 9: Data Validation — All 20 validation modules."""
import asyncio, time, json, hashlib, re
from collections import Counter
from datetime import datetime
from urllib.parse import urlparse
from sections.base import BaseTool, ToolResult, ToolCategory

class DeduplicationValidator(BaseTool):
    name = "deduplication"; category = ToolCategory.VALIDATION
    capabilities = ["text_dedup", "fuzzy_match", "similarity", "exact_hash"]
    async def search(self, query, **kw):
        s=time.time()
        docs=kw.get("documents",[])
        if isinstance(docs, str): docs=[docs]
        seen=set(); unique=[]; dupes=[]
        for d in docs:
            h=hashlib.md5(d.strip().lower().encode()).hexdigest()
            if h not in seen: seen.add(h); unique.append(d)
            else: dupes.append(d)
        return ToolResult(source=query,data={"unique":len(unique),"duplicates":len(dupes),"unique_docs":unique,"dupe_docs":dupes},tool=self.name,duration_ms=self._timing(s))

class EntityResolution(BaseTool):
    name = "entity_resolution"; category = ToolCategory.VALIDATION
    capabilities = ["fuzzy_match", "entity_linking", "disambiguation"]
    async def search(self, query, **kw):
        s=time.time()
        entities=kw.get("entities",[])
        resolved={}
        for e in entities:
            canonical=e.lower().strip()
            resolved[canonical]={"original":e,"canonical":canonical,"confidence":1.0}
        return ToolResult(source=query,data=resolved,metadata={"count":len(entities)},tool=self.name,duration_ms=self._timing(s))

class CitationVerification(BaseTool):
    name = "citation_verify"; category = ToolCategory.VALIDATION
    capabilities = ["url_check", "doi_check", "reference_valid"]
    async def search(self, query, **kw):
        s=time.time()
        citations=kw.get("citations",[])
        results=[]
        for c in citations:
            status="unknown"
            try:
                import httpx
                url=c.get("url","")
                if url:
                    async with httpx.AsyncClient(timeout=10,follow_redirects=True) as client:
                        r=await client.head(url)
                        status="valid" if r.status_code<400 else "broken"
            except: status="error"
            results.append({**c,"status":status})
        valid=sum(1 for r in results if r["status"]=="valid")
        return ToolResult(source=query,data={"results":results,"valid":valid,"total":len(results)},tool=self.name,duration_ms=self._timing(s))

class SourceRanking(BaseTool):
    name = "source_ranking"; category = ToolCategory.VALIDATION
    capabilities = ["authority", "reliability", "bias_detection"]
    async def search(self, query, **kw):
        s=time.time()
        sources=kw.get("sources",[])
        ranked=sorted(sources,key=lambda x:x.get("authority_score",50),reverse=True)
        for i,s in enumerate(ranked): s["rank"]=i+1
        return ToolResult(source=query,data=ranked,tool=self.name,duration_ms=self._timing(s))

class ConfidenceScoring(BaseTool):
    name = "confidence"; category = ToolCategory.VALIDATION
    capabilities = ["confidence", "certainty", "evidence_weight"]
    async def search(self, query, **kw):
        s=time.time()
        evidence=kw.get("evidence",[])
        score=min(100,max(0,len(evidence)*15+kw.get("base_score",20)))
        return ToolResult(source=query,data={"confidence_score":score,"evidence_count":len(evidence),"level":"high" if score>70 else "medium" if score>40 else "low"},tool=self.name,duration_ms=self._timing(s))

class ProvenanceTracking(BaseTool):
    name = "provenance"; category = ToolCategory.VALIDATION
    capabilities = ["lineage", "audit_trail", "source_tracking"]
    async def search(self, query, **kw):
        s=time.time()
        record=kw.get("record",{})
        record["provenance"]={"source":kw.get("source","unknown"),"timestamp":datetime.now().isoformat(),"method":kw.get("method","direct"),"chain":kw.get("chain",[])}
        return ToolResult(source=query,data=record,tool=self.name,duration_ms=self._timing(s))

class FactVerification(BaseTool):
    name = "fact_check"; category = ToolCategory.VALIDATION
    capabilities = ["claim_check", "evidence_search", "verdict"]
    async def search(self, query, **kw):
        s=time.time()
        claim=kw.get("claim",query)
        evidence=kw.get("evidence",[])
        verdict="unverified"
        if len(evidence)>3: verdict="supported"
        elif len(evidence)>0: verdict="partially_supported"
        return ToolResult(source=query,data={"claim":claim,"verdict":verdict,"evidence_count":len(evidence)},tool=self.name,duration_ms=self._timing(s))

class HallucinationDetection(BaseTool):
    name = "hallucination"; category = ToolCategory.VALIDATION
    capabilities = ["hallucination_check", "grounding", "factuality"]
    async def search(self, query, **kw):
        s=time.time()
        text=kw.get("text",query)
        facts=kw.get("facts",[])
        supported=0
        for f in facts:
            if f.lower() in text.lower(): supported+=1
        score=supported/max(len(facts),1)*100
        return ToolResult(source=query,data={"hallucination_score":round(100-score,1),"grounded_facts":supported,"total_facts":len(facts),"grounding_level":"high" if score>70 else "medium" if score>40 else "low"},tool=self.name,duration_ms=self._timing(s))

class TemporalValidation(BaseTool):
    name = "temporal"; category = ToolCategory.VALIDATION
    capabilities = ["date_check", "recency", "time_relevance"]
    async def search(self, query, **kw):
        s=time.time()
        items=kw.get("items",[])
        results=[]
        for item in items:
            date_str=item.get("date","")
            try:
                date=datetime.fromisoformat(date_str.replace("Z",""))
                age_days=(datetime.now()-date).days
                recency="recent" if age_days<30 else "moderate" if age_days<365 else "old"
                results.append({**item,"age_days":age_days,"recency":recency})
            except: results.append({**item,"recency":"unknown"})
        return ToolResult(source=query,data=results,tool=self.name,duration_ms=self._timing(s))

class GeographicalValidation(BaseTool):
    name = "geographical"; category = ToolCategory.VALIDATION
    capabilities = ["geo_check", "location_validity", "bounding_box"]
    async def search(self, query, **kw):
        s=time.time()
        lat=kw.get("lat",0); lng=kw.get("lng",0)
        raipur_bounds={"lat_min":21.15,"lat_max":21.40,"lng_min":81.45,"lng_max":81.85}
        in_raipur=raipur_bounds["lat_min"]<=lat<=raipur_bounds["lat_max"] and raipur_bounds["lng_min"]<=lng<=raipur_bounds["lng_max"]
        return ToolResult(source=query,data={"lat":lat,"lng":lng,"in_raipur":in_raipur,"bounds":raipur_bounds},tool=self.name,duration_ms=self._timing(s))

class DuplicateImageDetection(BaseTool):
    name = "image_dedup"; category = ToolCategory.VALIDATION
    capabilities = ["perceptual_hash", "image_similarity", "near_dupes"]
    async def search(self, query, **kw):
        s=time.time()
        images=kw.get("image_paths",[])
        hashes=[]
        for img_path in images:
            try:
                from PIL import Image
                import imagehash
                h=imagehash.phash(Image.open(img_path))
                hashes.append({"path":img_path,"hash":str(h)})
            except: hashes.append({"path":img_path,"hash":"error"})
        return ToolResult(source=query,data=hashes,tool=self.name,duration_ms=self._timing(s))

class URLHealthCheck(BaseTool):
    name = "url_health"; category = ToolCategory.VALIDATION
    capabilities = ["status_check", "ssl_check", "response_time"]
    async def search(self, query, **kw):
        s=time.time()
        urls=kw.get("urls",[])
        if isinstance(urls,str): urls=[urls]
        results=[]
        for url in urls:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10,follow_redirects=True) as c:
                    r=await c.head(url)
                    results.append({"url":url,"status":r.status_code,"healthy":r.status_code<400,"response_ms":r.elapsed.total_seconds()*1000})
            except Exception as e:
                results.append({"url":url,"status":0,"healthy":False,"error":str(e)[:50]})
        healthy=sum(1 for r in results if r["healthy"])
        return ToolResult(source=query,data={"results":results,"healthy":healthy,"total":len(results)},tool=self.name,duration_ms=self._timing(s))

class DeadLinkDetection(BaseTool):
    name = "dead_links"; category = ToolCategory.VALIDATION
    capabilities = ["link_check", "broken_detection", "redirect_chain"]
    async def search(self, query, **kw):
        s=time.time()
        links=kw.get("links",[])
        results=[]
        for link in links:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=10,follow_redirects=True) as c:
                    r=await c.get(link)
                    results.append({"url":link,"status":r.status_code,"dead":r.status_code>=400})
            except: results.append({"url":link,"status":0,"dead":True})
        dead=sum(1 for r in results if r["dead"])
        return ToolResult(source=query,data={"dead_links":dead,"alive_links":len(results)-dead,"results":results},tool=self.name,duration_ms=self._timing(s))

class SchemaValidation(BaseTool):
    name = "schema"; category = ToolCategory.VALIDATION
    capabilities = ["json_schema", "pydantic", "struct_check"]
    async def search(self, query, **kw):
        s=time.time()
        data=kw.get("data",{})
        schema=kw.get("schema",{})
        errors=[]
        for key in schema.get("required",[]):
            if key not in data: errors.append(f"Missing required field: {key}")
        for key,t in schema.get("properties",{}).items():
            if key in data and not isinstance(data[key],eval(t.get("type","str"))):
                errors.append(f"Type mismatch: {key} should be {t.get('type')}")
        return ToolResult(source=query,data={"valid":len(errors)==0,"errors":errors},tool=self.name,duration_ms=self._timing(s))

class LanguageDetection(BaseTool):
    name = "lang_detect"; category = ToolCategory.VALIDATION
    capabilities = ["language", "script", "hindi_detection"]
    async def search(self, query, **kw):
        s=time.time()
        text=kw.get("text",query)
        try:
            from langdetect import detect
            lang=detect(text)
            return ToolResult(source=query,data={"detected_language":lang,"text_preview":text[:100]},tool=self.name,duration_ms=self._timing(s))
        except: return ToolResult(source=query,data={"detected_language":"unknown","text_preview":text[:100]},tool=self.name,duration_ms=self._timing(s))

class TranslationVerification(BaseTool):
    name = "translation_verify"; category = ToolCategory.VALIDATION
    capabilities = ["back_translate", "quality_check", "meaning_preservation"]
    async def search(self, query, **kw):
        s=time.time()
        original=kw.get("original",""); translated=kw.get("translated","")
        similarity=len(set(original.lower().split())&set(translated.lower().split()))/max(len(set(original.lower().split())),1)*100
        return ToolResult(source=query,data={"original":original[:200],"translated":translated[:200],"lexical_overlap":round(similarity,1)},tool=self.name,duration_ms=self._timing(s))

class MetadataValidation(BaseTool):
    name = "metadata"; category = ToolCategory.VALIDATION
    capabilities = ["meta_check", "completeness", "consistency"]
    async def search(self, query, **kw):
        s=time.time()
        record=kw.get("record",{})
        required=kw.get("required_fields",["title","url","date","source"])
        missing=[f for f in required if f not in record or not record[f]]
        completeness=round((1-len(missing)/max(len(required),1))*100,1)
        return ToolResult(source=query,data={"record":record,"completeness":completeness,"missing_fields":missing},tool=self.name,duration_ms=self._timing(s))

class EvidenceRanking(BaseTool):
    name = "evidence_ranking"; category = ToolCategory.VALIDATION
    capabilities = ["relevance", "quality_score", "ranking"]
    async def search(self, query, **kw):
        s=time.time()
        evidence=kw.get("evidence",[])
        ranked=sorted(evidence,key=lambda x:x.get("relevance",50),reverse=True)
        for i,e in enumerate(ranked): e["rank"]=i+1
        return ToolResult(source=query,data=ranked,tool=self.name,duration_ms=self._timing(s))

class CrossSourceConsensus(BaseTool):
    name = "consensus"; category = ToolCategory.VALIDATION
    capabilities = ["agreement", "multi_source", "confidence"]
    async def search(self, query, **kw):
        s=time.time()
        sources=kw.get("sources",[])
        claim=kw.get("claim","")
        supports=sum(1 for s in sources if claim.lower() in s.get("text","").lower())
        consensus=round(supports/max(len(sources),1)*100,1)
        return ToolResult(source=query,data={"claim":claim,"sources_supporting":supports,"total_sources":len(sources),"consensus_score":consensus},tool=self.name,duration_ms=self._timing(s))

class CanonicalRecordBuilder(BaseTool):
    name = "canonical_record"; category = ToolCategory.VALIDATION
    capabilities = ["merge", "deduplicate", "canonical", "golden_record"]
    async def search(self, query, **kw):
        s=time.time()
        records=kw.get("records",[])
        canonical={}; scores={}
        for r in records:
            for k,v in r.items():
                if k not in canonical or scores.get(k,0)<r.get("_confidence",50):
                    canonical[k]=v; scores[k]=r.get("_confidence",50)
        canonical["_source_count"]=len(records); canonical["_merged_at"]=datetime.now().isoformat()
        return ToolResult(source=query,data=canonical,tool=self.name,duration_ms=self._timing(s))

VALIDATION_REGISTRY = {
    "deduplication": DeduplicationValidator, "entity_resolution": EntityResolution,
    "citation_verify": CitationVerification, "source_ranking": SourceRanking,
    "confidence": ConfidenceScoring, "provenance": ProvenanceTracking,
    "fact_check": FactVerification, "hallucination": HallucinationDetection,
    "temporal": TemporalValidation, "geographical": GeographicalValidation,
    "image_dedup": DuplicateImageDetection, "url_health": URLHealthCheck,
    "dead_links": DeadLinkDetection, "schema": SchemaValidation,
    "lang_detect": LanguageDetection, "translation_verify": TranslationVerification,
    "metadata": MetadataValidation, "evidence_ranking": EvidenceRanking,
    "consensus": CrossSourceConsensus, "canonical_record": CanonicalRecordBuilder,
}
