/*
  My Family Should Know — multi-tenant single-submit Google gateway.
  Streamlit sends one lightweight HTTPS POST when a family explicitly exports.
  Binary documents are uploaded directly to Google Drive by Streamlit using resumable uploads.
  Apps Script only writes structured data/Drive links to Sheets and runs reminders.
  Apps Script never exposes one tenant's data to another tenant through the app.
*/

const PROP = PropertiesService.getScriptProperties();
const DATA_SHEET = 'Family_Data';
const REMINDER_SHEET = 'Reminders';
const CONTACT_SHEET = 'Contacts';
const CONFIG_SHEET = 'Reminder_Config';
const LOG_SHEET = 'Sync_Log';
const TENANT_SHEET = 'Tenant_Status';
const NONCE_SHEET = 'Request_Nonce';
const REMINDER_LOG_SHEET = 'Reminder_Log';


function withBackoff(fn, label, attempts) {
  attempts = attempts || 6;
  let delay = 500;
  let last = null;
  for (let i = 0; i < attempts; i++) {
    try { return fn(); }
    catch (err) {
      last = err;
      const msg = String(err && err.message ? err.message : err).toLowerCase();
      const retryable = msg.indexOf('429') !== -1 || msg.indexOf('quota') !== -1 || msg.indexOf('rate limit') !== -1 || msg.indexOf('service invoked too many times') !== -1 || msg.indexOf('temporarily unavailable') !== -1 || msg.indexOf('timeout') !== -1;
      if (!retryable || i === attempts - 1) throw err;
      Utilities.sleep(delay + Math.floor(Math.random() * 500));
      delay = Math.min(delay * 2, 16000);
    }
  }
  throw last;
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    if (!e || !e.postData || !e.postData.contents) return jsonOut({success:false,error:'Empty request.'});
    const envelope = JSON.parse(e.postData.contents);
    const payload = envelope && envelope.payload;
    const signature = String((envelope && envelope.auth_signature) || '');
    const expected = PROP.getProperty('SYNC_TOKEN') || '';
    if (!expected || !payload || !signature) return jsonOut({success:false,error:'Unauthorized sync request.'});
    validatePayload(payload);
    validateRequestFreshness(payload);
    const signedBody = JSON.stringify(payload);
    const expectedSignature = bytesToHex(Utilities.computeHmacSha256Signature(signedBody, expected));
    if (!constantTimeEqual(signature, expectedSignature)) return jsonOut({success:false,error:'Unauthorized sync request.'});

    lock.waitLock(30000);
    const ss = getSpreadsheet();
    // Sync_Log is the durable idempotency ledger for completed submissions.
    // This avoids one permanent Script Property per successful submission.
    if (getSyncStatus(ss, payload.submission_id).status === 'SUCCESS') {
      return jsonOut({success:true,record_id:payload.submission_id,duplicate:true,rows:0,attachments:0});
    }
    // Consume the nonce only after authentication and under the script lock, so
    // concurrent identical requests cannot both pass the replay check.
    consumeNonce(ss, payload);
    const result = syncSubmission(payload, ss);
    return jsonOut({success:true,record_id:result.record_id,duplicate:false,rows:result.rows,attachments:result.attachments});
  } catch (err) {
    console.error(err && err.stack ? err.stack : err);
    return jsonOut({success:false,error:String(err && err.message ? err.message : err)});
  } finally {
    try { lock.releaseLock(); } catch (_) {}
  }
}

function validateRequestFreshness(p) {
  const ts = Number(p.auth_timestamp);
  const nonce = String(p.auth_nonce || '');
  if (!isFinite(ts) || !nonce || nonce.length < 16 || nonce.length > 128) throw new Error('Invalid request authentication metadata.');
  if (Math.abs(Date.now() - ts) > 10 * 60 * 1000) throw new Error('Request authentication window expired. Retry the submission.');
}

function consumeNonce(ss, p) {
  const nonce = String(p.auth_nonce || '');
  const tenantId = String(p.tenant_id || '');
  const sh = getOrCreateSheet(ss, NONCE_SHEET, ['Tenant ID','Nonce','Created At']);
  const now = Date.now();
  const cutoff = now - 10 * 60 * 1000;
  if (sh.getLastRow() >= 2) {
    const values = sh.getRange(2,1,sh.getLastRow()-1,3).getValues();
    const fresh=[];
    for (let i = 0; i < values.length; i++) {
      const created = new Date(values[i][2]).getTime();
      if (!isFinite(created) || created < cutoff) continue;
      if (String(values[i][0]) === tenantId && String(values[i][1]) === nonce) throw new Error('Duplicate request detected. Retry the submission.');
      fresh.push(values[i]);
    }
    sh.getRange(2,1,values.length,3).clearContent();
    if(fresh.length) sh.getRange(2,1,fresh.length,3).setValues(fresh);
  }
  sh.getRange(sh.getLastRow()+1,1,1,3).setValues([[tenantId,nonce,new Date(now).toISOString()]]);
  sh.setFrozenRows(1);
}

function constantTimeEqual(a,b) {
  a=String(a||''); b=String(b||'');
  let diff=a.length^b.length;
  const n=Math.max(a.length,b.length);
  for(let i=0;i<n;i++) diff|=(a.charCodeAt(i)||0)^(b.charCodeAt(i)||0);
  return diff===0;
}
function bytesToHex(bytes) {
  return bytes.map(function(b){ const v=(b<0?b+256:b).toString(16); return v.length===1?'0'+v:v; }).join('');
}

function validatePayload(p) {
  if (!p.version || !p.submission_id || !p.tenant_id) throw new Error('Invalid submission payload.');
  if (!/^[a-f0-9]{32}$/i.test(String(p.tenant_id))) throw new Error('Invalid tenant identifier.');
  if (!/^[a-f0-9]{32}$/i.test(String(p.submission_id))) throw new Error('Invalid submission identifier.');
  if (!Array.isArray(p.records) || !p.attachment_links || typeof p.attachment_links !== 'object') throw new Error('Invalid record or attachment-link payload.');
  if (!p.reminders || !Array.isArray(p.reminders.contacts)) throw new Error('Invalid reminder configuration.');
  if (p.records.length > 5000) throw new Error('Submission contains too many records.');
  if (Object.keys(p.attachment_links).length > 5000) throw new Error('Submission contains too many attachment links.');
  p.records.forEach(function(r){ if (!r.record_id || !r.section_key) throw new Error('Invalid record entry.'); });
  Object.keys(p.attachment_links).forEach(function(recordId){
    const a=p.attachment_links[recordId]||{};
    if (a.drive_file_id && !/^[A-Za-z0-9_-]+$/.test(String(a.drive_file_id))) throw new Error('Invalid Drive file identifier.');
    if (a.drive_url && !/^https:\/\/drive\.google\.com\//.test(String(a.drive_url))) throw new Error('Invalid Drive URL.');
  });
}

function syncSubmission(p, ss) {
  const attachmentLinks = p.attachment_links || {};
  // Current-state sheets are versioned by submission ID. Write the complete
  // replacement first, then remove older versions. If a retry happens after
  // a partial write, rows from the same submission are removed before that
  // submission is rewritten, preventing duplicates.
  writeSyncStatus(ss, p, 'PROCESSING', '');

  try {
    // A retry of the same submission must first remove only its own partial
    // rows. The previous successful/current submission remains untouched.
    removeSubmissionRows(ss, DATA_SHEET, p.submission_id, p.tenant_id);
    removeSubmissionRows(ss, REMINDER_SHEET, p.submission_id, p.tenant_id);
    removeVersionRows(ss, CONFIG_SHEET, p.tenant_id, p.submission_id, 4);
    removeVersionRows(ss, CONTACT_SHEET, p.tenant_id, p.submission_id, 5);
    removeVersionRows(ss, TENANT_SHEET, p.tenant_id, p.submission_id, 5);
    removeSubmissionRows(ss, REMINDER_LOG_SHEET, p.submission_id, p.tenant_id);

    writeFamilyData(ss, p.records, attachmentLinks, p.submission_id, p.tenant_id);
    writeReminders(ss, p);
    upsertTenantConfig(ss, p.tenant_id, p.reminders, p.submission_id);
    upsertTenantContacts(ss, p.tenant_id, p.reminders.contacts, p.submission_id);
    ensureReminderTrigger();

    // Publish the new submission before cleanup. The active-submission marker
    // is the source of truth used by reminderJob, so a cleanup failure can
    // never make the old (partially cleaned) submission active again.
    upsertTenantStatus(ss, p.tenant_id, p.submission_id, p.tenant_name || '');

    // Cleanup is deliberately non-fatal. Google Sheets row deletion is not
    // transactional; if a cleanup operation fails after the new state is
    // published, retaining some stale rows is safer than deleting the new
    // state in the error handler. They will be removed by the next successful
    // submission.
    try {
      removeTenantRowsExceptSubmission(ss, DATA_SHEET, p.tenant_id, p.submission_id);
      removeTenantRowsExceptSubmission(ss, REMINDER_SHEET, p.tenant_id, p.submission_id);
      removeTenantRowsExceptSubmission(ss, REMINDER_LOG_SHEET, p.tenant_id, p.submission_id);
      removeVersionRowsExcept(ss, CONFIG_SHEET, p.tenant_id, p.submission_id, 4);
      removeVersionRowsExcept(ss, CONTACT_SHEET, p.tenant_id, p.submission_id, 5);
      removeVersionRowsExcept(ss, TENANT_SHEET, p.tenant_id, p.submission_id, 5);
    } catch (cleanupErr) {
      console.error('Current-state cleanup deferred: '+(cleanupErr && cleanupErr.message ? cleanupErr.message : cleanupErr));
    }

    writeSyncStatus(ss, p, 'SUCCESS', '');
    trimSyncLogForTenant(ss, p.tenant_id, 100);

    return {record_id:p.submission_id,rows:p.records.length,attachments:Object.keys(attachmentLinks).length};
  } catch (err) {
    // If publication has not happened yet, discard only this submission's
    // staged rows. Once Tenant_Status points at this submission, never delete
    // its rows from the error path: the new state must remain recoverable.
    const active = getActiveSubmissionId(ss, p.tenant_id);
    if (active !== String(p.submission_id)) {
      removeSubmissionRows(ss, DATA_SHEET, p.submission_id, p.tenant_id);
      removeSubmissionRows(ss, REMINDER_SHEET, p.submission_id, p.tenant_id);
      removeVersionRows(ss, CONFIG_SHEET, p.tenant_id, p.submission_id, 4);
      removeVersionRows(ss, CONTACT_SHEET, p.tenant_id, p.submission_id, 5);
      removeVersionRows(ss, TENANT_SHEET, p.tenant_id, p.submission_id, 5);
      removeSubmissionRows(ss, REMINDER_LOG_SHEET, p.submission_id, p.tenant_id);
    }
    writeSyncStatus(ss, p, 'FAILED', String(err && err.message ? err.message : err));
    throw err;
  }
}

function getSpreadsheet() {
  const id = PROP.getProperty('SPREADSHEET_ID');
  if (!id) throw new Error('SPREADSHEET_ID is not configured in Apps Script Properties.');
  return SpreadsheetApp.openById(id);
}
function getOrCreateSheet(ss,name,headers) {
  let sh=ss.getSheetByName(name);
  if(!sh) { sh=ss.insertSheet(name); if(headers && headers.length) sh.getRange(1,1,1,headers.length).setValues([headers]); return sh; }
  if(headers && headers.length) {
    const current=sh.getLastColumn() ? sh.getRange(1,1,1,sh.getLastColumn()).getValues()[0].map(String) : [];
    const expected=headers.map(String);
    const same=current.length===expected.length && expected.every(function(v,i){return current[i]===v;});
    if(!same) {
      const legacyName=name+'_Legacy_'+Utilities.formatDate(new Date(),Session.getScriptTimeZone()||'Asia/Kolkata','yyyyMMdd_HHmmss');
      sh.setName(legacyName); sh=ss.insertSheet(name); sh.getRange(1,1,1,headers.length).setValues([headers]);
    } else if(sh.getLastRow()===0) sh.getRange(1,1,1,headers.length).setValues([headers]);
  }
  return sh;
}
function removeSubmissionRows(ss,sheetName,submissionId,tenantId) {
  const sh=ss.getSheetByName(sheetName); if(!sh || sh.getLastRow()<2) return;
  const lastCol=sh.getLastColumn(); if(!lastCol) return;
  const values=sh.getRange(2,1,sh.getLastRow()-1,lastCol).getValues();
  for(let i=values.length-1;i>=0;i--) {
    if(String(values[i][0])===String(tenantId) && String(values[i][1])===String(submissionId)) sh.deleteRow(i+2);
  }
}
function removeTenantRows(ss,sheetName,tenantId) {
  const sh=ss.getSheetByName(sheetName); if(!sh || sh.getLastRow()<2) return;
  const lastCol=sh.getLastColumn(); if(!lastCol) return;
  const values=sh.getRange(2,1,sh.getLastRow()-1,lastCol).getValues();
  for(let i=values.length-1;i>=0;i--) if(String(values[i][0])===String(tenantId)) sh.deleteRow(i+2);
}
function removeTenantRowsExceptSubmission(ss,sheetName,tenantId,submissionId) {
  const sh=ss.getSheetByName(sheetName); if(!sh || sh.getLastRow()<2) return;
  const lastCol=sh.getLastColumn(); if(!lastCol) return;
  const values=sh.getRange(2,1,sh.getLastRow()-1,lastCol).getValues();
  for(let i=values.length-1;i>=0;i--) {
    if(String(values[i][0])===String(tenantId) && String(values[i][1])!==String(submissionId)) sh.deleteRow(i+2);
  }
}
function getOrCreateFolder(parent,name) { const it=parent.getFoldersByName(name); return it.hasNext()?it.next():parent.createFolder(name); }
function deleteFilesInFolder(folder) { const it=folder.getFiles(); while(it.hasNext()) it.next().setTrashed(true); }

function trimSyncLogForTenant(ss, tenantId, keepCount) {
  const sh=ss.getSheetByName(LOG_SHEET);
  if(!sh || sh.getLastRow()<2) return;
  keepCount=keepCount||100;
  const lastCol=sh.getLastColumn();
  const values=sh.getRange(2,1,sh.getLastRow()-1,lastCol).getValues();
  const matches=[];
  for(let i=0;i<values.length;i++) {
    if(String(values[i][0])===String(tenantId)) matches.push({index:i,time:new Date(values[i][2]).getTime()||0});
  }
  if(matches.length<=keepCount) return;
  matches.sort(function(a,b){return b.time-a.time || b.index-a.index;});
  const keep={};
  matches.slice(0,keepCount).forEach(function(x){keep[x.index]=true;});
  const out=values.filter(function(row,i){return String(row[0])!==String(tenantId) || keep[i];});
  sh.getRange(2,1,values.length,lastCol).clearContent();
  if(out.length) sh.getRange(2,1,out.length,lastCol).setValues(out);
}

function getActiveSubmissionId(ss,tenantId) {
  const sh=ss.getSheetByName(TENANT_SHEET);
  if(!sh || sh.getLastRow()<2) return '';
  const values=sh.getRange(2,1,sh.getLastRow()-1,3).getValues();
  for(let i=values.length-1;i>=0;i--) {
    if(String(values[i][0])===String(tenantId)) return String(values[i][2]||'');
  }
  return '';
}
function getSyncStatus(ss,submissionId) {
  const sh=ss.getSheetByName(LOG_SHEET); if(!sh || sh.getLastRow()<2) return {status:'',tenantId:''};
  const values=sh.getRange(2,1,sh.getLastRow()-1,7).getValues();
  for(let i=values.length-1;i>=0;i--) if(String(values[i][1])===String(submissionId)) return {status:String(values[i][6]||''),tenantId:String(values[i][0]||'')};
  return {status:'',tenantId:''};
}
function ensureHeader(sh,headers) { if(sh.getLastRow()===0) sh.getRange(1,1,1,headers.length).setValues([headers]); }

function writeFamilyData(ss,records,links,submissionId,tenantId) {
  const headers=['Tenant ID','Submission ID','Record ID','Page','Section','Row Label','Field','Value','Attachment','Record Created','Record Updated'];
  const rows=[];
  (records||[]).forEach(function(r){
    const sec=sectionInfo(r.section_key);
    Object.keys(r.values||{}).forEach(function(field){
      rows.push([tenantId,submissionId,r.record_id,sec.page,sec.title,r.row_label||'',field,String(r.values[field]==null?'':r.values[field]),(links[r.record_id]||{}).drive_url||'',r.created_at||'',r.updated_at||'']);
    });
    if(r.attachment_name && !links[r.record_id]) rows.push([tenantId,submissionId,r.record_id,sec.page,sec.title,r.row_label||'','Attachment',r.attachment_name,'',r.created_at||'',r.updated_at||'']);
  });
  const sh=getOrCreateSheet(ss,DATA_SHEET,headers); ensureHeader(sh,headers);
  if(rows.length) sh.getRange(sh.getLastRow()+1,1,rows.length,headers.length).setValues(rows);
  sh.setFrozenRows(1);
}

function writeReminders(ss,p) {
  const headers=['Tenant ID','Submission ID','Section Key','Section','Record ID','Record Label','Field','Due Date','Days Until','Status','Reminder Windows','Overdue Enabled'];
  const rows=[]; const today=startOfDay(new Date());
  const windows=(p.reminders.days_before||[]).map(Number).filter(function(x){return x>=0;}).sort(function(a,b){return b-a;});
  const overdueEnabled=p.reminders.overdue_enabled!==false;
  (p.records||[]).forEach(function(r){
    const mapped=(p.reminders.reminder_fields||{})[r.section_key]||[];
    mapped.forEach(function(field){
      const due=parseDate((r.values||{})[field]); if(!due) return;
      const delta=Math.round((due-today)/86400000);
      const status=delta<0?'OVERDUE':(delta===0?'DUE TODAY':'UPCOMING');
      rows.push([p.tenant_id,p.submission_id,r.section_key,sectionInfo(r.section_key).title,r.record_id,r.row_label||sectionInfo(r.section_key).title,field,formatDate(due),delta,status,windows.join(','),overdueEnabled?'YES':'NO']);
    });
  });
  const sh=getOrCreateSheet(ss,REMINDER_SHEET,headers); ensureHeader(sh,headers);
  if(rows.length) sh.getRange(sh.getLastRow()+1,1,rows.length,headers.length).setValues(rows);
  sh.setFrozenRows(1);
}

function upsertTenantConfig(ss,tenantId,settings,submissionId) {
  const sh=getOrCreateSheet(ss,CONFIG_SHEET,['Tenant ID','Setting','Value','Submission ID']);
  const rows=[['Enabled',settings.enabled?'YES':'NO'],['Email Enabled',settings.email_enabled?'YES':'NO'],['Overdue Enabled',settings.overdue_enabled?'YES':'NO'],['Reminder Windows',(settings.days_before||[]).join(',')]].map(function(r){return [tenantId,r[0],r[1],submissionId];});
  if(rows.length) sh.getRange(sh.getLastRow()+1,1,rows.length,4).setValues(rows); sh.setFrozenRows(1);
}
function upsertTenantContacts(ss,tenantId,contacts,submissionId) {
  const sh=getOrCreateSheet(ss,CONTACT_SHEET,['Tenant ID','Name','Email','Enabled','Submission ID']);
  const rows=(contacts||[]).filter(function(c){return c.email;}).map(function(c){return [tenantId,c.name||'',c.email||'','YES',submissionId];});
  if(rows.length) sh.getRange(sh.getLastRow()+1,1,rows.length,5).setValues(rows); sh.setFrozenRows(1);
}
function upsertTenantStatus(ss,tenantId,submissionId,name) {
  const sh=getOrCreateSheet(ss,TENANT_SHEET,['Tenant ID','Family / Account','Active Submission ID','Updated At','Submission ID']);
  sh.getRange(sh.getLastRow()+1,1,1,5).setValues([[tenantId,name||'',submissionId,new Date().toISOString(),submissionId]]); sh.setFrozenRows(1);
}
function removeVersionRows(ss,sheetName,tenantId,versionId,versionCol) {
  const sh=ss.getSheetByName(sheetName); if(!sh || sh.getLastRow()<2) return;
  const lastCol=sh.getLastColumn(); if(lastCol<versionCol) return;
  const values=sh.getRange(2,1,sh.getLastRow()-1,lastCol).getValues();
  for(let i=values.length-1;i>=0;i--) {
    if(String(values[i][0])===String(tenantId) && String(values[i][versionCol-1]||'')===String(versionId)) sh.deleteRow(i+2);
  }
}
function removeVersionRowsExcept(ss,sheetName,tenantId,versionId,versionCol) {
  const sh=ss.getSheetByName(sheetName); if(!sh || sh.getLastRow()<2) return;
  const lastCol=sh.getLastColumn(); if(lastCol<versionCol) return;
  const values=sh.getRange(2,1,sh.getLastRow()-1,lastCol).getValues();
  for(let i=values.length-1;i>=0;i--) {
    if(String(values[i][0])===String(tenantId) && String(values[i][versionCol-1]||'')!==String(versionId)) sh.deleteRow(i+2);
  }
}
function writeSyncStatus(ss,p,status,folderUrl) {
  const sh=getOrCreateSheet(ss,LOG_SHEET,['Tenant ID','Submission ID','Submitted At','Records','Attachments','Drive Root','Status']);
  const values=sh.getLastRow()>=2?sh.getRange(2,1,sh.getLastRow()-1,7).getValues():[];
  for(let i=values.length-1;i>=0;i--) if(String(values[i][0])===String(p.tenant_id)&&String(values[i][1])===String(p.submission_id)) { sh.getRange(i+2,1,1,7).setValues([[p.tenant_id,p.submission_id,p.submitted_at,p.records.length,Object.keys(p.attachment_links||{}).length,folderUrl,status]]); return; }
  sh.getRange(sh.getLastRow()+1,1,1,7).setValues([[p.tenant_id,p.submission_id,p.submitted_at,p.records.length,Object.keys(p.attachment_links||{}).length,folderUrl,status]]);
}

function reminderLogKey(tenantId, submissionId, recordId, field, dueDate, windowKey, email) {
  return [tenantId,submissionId,recordId,field,formatDate(dueDate),windowKey,String(email).toLowerCase()].join('|');
}
function readReminderLog(ss) {
  const out={}; const sh=ss.getSheetByName(REMINDER_LOG_SHEET);
  if(!sh || sh.getLastRow()<2) return out;
  const values=sh.getRange(2,1,sh.getLastRow()-1,8).getValues();
  values.forEach(function(r){
    const due=parseDate(r[4]);
    if(!due) return;
    const key=reminderLogKey(String(r[0]||''),String(r[1]||''),String(r[2]||''),String(r[3]||''),due,String(r[5]||''),String(r[6]||''));
    if(key) out[key]=true;
  });
  return out;
}
function appendReminderLog(ss,tenantId,submissionId,recordId,field,dueDate,windowKey,email) {
  const sh=getOrCreateSheet(ss,REMINDER_LOG_SHEET,['Tenant ID','Submission ID','Record ID','Field','Due Date','Window','Email','Sent At']);
  sh.getRange(sh.getLastRow()+1,1,1,8).setValues([[tenantId,submissionId,recordId,field,formatDate(dueDate),windowKey,String(email).toLowerCase(),new Date().toISOString()]]);
  sh.setFrozenRows(1);
}

function reminderJob() {
  const ss=getSpreadsheet(); const rem=ss.getSheetByName(REMINDER_SHEET), con=ss.getSheetByName(CONTACT_SHEET), cfg=ss.getSheetByName(CONFIG_SHEET), stat=ss.getSheetByName(TENANT_SHEET);
  if(!rem||!con||!cfg||!stat||rem.getLastRow()<2||stat.getLastRow()<2) return;
  const statuses=stat.getRange(2,1,stat.getLastRow()-1,4).getValues();
  const contacts=readContactsByTenant(con); const configs=readConfigsByTenant(cfg);
  const reminders=rem.getRange(2,1,rem.getLastRow()-1,12).getValues(); const sent=readReminderLog(ss); const today=startOfDay(new Date());
  statuses.forEach(function(sr){
    const tenantId=String(sr[0]||''), activeSubmission=String(sr[2]||''); if(!tenantId||!activeSubmission) return;
    const settings=configs[tenantId]||{enabled:true,emailEnabled:true,overdueEnabled:true,windows:[30,15,7,1]};
    if(!settings.enabled||!settings.emailEnabled) return;
    const tenantContacts=contacts[tenantId]||[]; if(!tenantContacts.length) return;
    reminders.forEach(function(r){
      if(String(r[0])!==tenantId||String(r[1])!==activeSubmission) return;
      const due=parseDate(r[7]); if(!due) return;
      const delta=Math.round((due-today)/86400000);
      const allowed=delta<0?settings.overdueEnabled:settings.windows.indexOf(delta)!==-1; if(!allowed) return;
      const windowKey=delta<0?'OVERDUE':String(delta);
      tenantContacts.forEach(function(c){
        const key=reminderLogKey(tenantId,r[1],r[4],r[6],due,windowKey,c.email);
        if(sent[key]) return;
        const timing=delta<0?('overdue by '+Math.abs(delta)+' day(s)'):(delta===0?'is due today':('is due in '+delta+' day(s)'));
        const subject='Family Reminder: '+r[5]+' '+timing;
        const body='Hello '+c.name+',\n\nThis is an automatic reminder from My Family Should Know.\n\nRecord: '+r[5]+'\nCategory: '+r[3]+'\nDate field: '+r[6]+'\nDue / expiry date: '+formatDate(due)+'\n\nPlease take the required action if renewal, payment, expiry or another follow-up is needed.\n\n— My Family Should Know';
        try { MailApp.sendEmail(c.email,subject,body); appendReminderLog(ss,tenantId,r[1],r[4],r[6],due,windowKey,c.email); sent[key]=true; } catch(err) { console.error('Reminder failed for '+c.email+': '+err); }
      });
    });
  });
}
function readConfigsByTenant(sh) {
  const out={}; if(sh.getLastRow()<2) return out;
  sh.getRange(2,1,sh.getLastRow()-1,Math.min(3,sh.getLastColumn())).getValues().forEach(function(r){ const t=String(r[0]||''),k=String(r[1]||''),v=String(r[2]||''); if(!t)return; if(!out[t])out[t]={enabled:true,emailEnabled:true,overdueEnabled:true,windows:[30,15,7,1]}; if(k==='Enabled')out[t].enabled=v!=='NO'; else if(k==='Email Enabled')out[t].emailEnabled=v!=='NO'; else if(k==='Overdue Enabled')out[t].overdueEnabled=v!=='NO'; else if(k==='Reminder Windows')out[t].windows=v.split(',').map(Number).filter(function(x){return !isNaN(x);}); });
  return out;
}
function readContactsByTenant(sh) {
  const out={}; if(sh.getLastRow()<2) return out;
  sh.getRange(2,1,sh.getLastRow()-1,Math.min(4,sh.getLastColumn())).getValues().forEach(function(r){ if(String(r[3]).toUpperCase()!=='YES'||!r[2])return; const t=String(r[0]||''); if(!out[t])out[t]=[]; out[t].push({name:String(r[1]||'Family member'),email:String(r[2])}); });
  return out;
}
function ensureReminderTrigger() {
  const triggers=ScriptApp.getProjectTriggers();
  const exists=triggers.some(function(t){return t.getHandlerFunction()==='reminderJob';});
  if(!exists) ScriptApp.newTrigger('reminderJob').timeBased().everyDays(1).atHour(9).create();
  PROP.setProperty('REMINDER_TRIGGER_READY','1');
}
function parseDate(v) { if(!v)return null; if(Object.prototype.toString.call(v)==='[object Date]'&&!isNaN(v))return startOfDay(v); const s=String(v).trim(); const m=s.match(/^(\d{4})[-\/](\d{1,2})[-\/](\d{1,2})$/); if(m)return new Date(Number(m[1]),Number(m[2])-1,Number(m[3])); const d=new Date(s); return isNaN(d)?null:startOfDay(d); }
function startOfDay(d){const x=new Date(d);x.setHours(0,0,0,0);return x;}
function formatDate(d){return Utilities.formatDate(d,Session.getScriptTimeZone()||'Asia/Kolkata','yyyy-MM-dd');}
function safeName(s){return String(s).replace(/[^a-zA-Z0-9._ -]/g,'_').slice(0,120);}
function jsonOut(obj){return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);}
function sectionInfo(key){const map={ready_reference:[2,'Ready Reference'],mobile_phone_self:[2,'Mobile / Phone (Self)'],document_details:[2,'Document Details'],important_documents:[3,'Location of Important Documents'],lic_policy:[3,'Insurance - LIC Policy Details'],medi_claim:[4,'Medi Claim Policy Details'],vehicle_insurance:[4,'Vehicle Insurance Policy Details'],fire_burglary:[4,'Fire / Burglary Insurance Details'],bank_accounts:[5,'Bank Accounts'],deposits:[5,'Fixed Deposit / Recurring Deposit / Company Deposit'],shares_units:[6,'Shares / Unity / Debentures / Bonds'],lockers:[6,'Lockers'],ppf:[7,'Public Provident Fund (PPF)'],pension:[7,'Pension A/C.'],atm_debit:[7,'ATM / Debit Card Details'],credit_cards:[7,'Credit Card Details'],pan_cards:[8,'PAN Card Details'],passports:[8,'Passport Details'],electricity:[8,'Electricity Details'],gas_pipeline:[8,'Gas Pipe Line Details'],gas_cylinder:[8,'Gas Cylinder Agency Service Details'],landline:[9,'Land Line Details'],driving_license:[9,'Driving License Details'],ration_card:[9,'Ration Card Details'],aadhaar:[9,'Aadhar Card - UID Details'],election_id:[10,'Election Identity Card - Details'],house_property:[10,'House Property'],house_tax:[10,'House Tax Details'],income_tax:[10,'Income Tax'],will:[11,'Will'],power_of_attorney:[11,'Power of Attorney'],debt_liabilities:[11,'My Debt / Liabilities']};const x=map[key]||[0,key];return {page:x[0],title:x[1]};}
