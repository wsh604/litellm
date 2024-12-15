"use strict";(self.webpackChunk_N_E=self.webpackChunk_N_E||[]).push([[939],{38939:function(e,t,o){o.d(t,{$I:function(){return G},AZ:function(){return B},Au:function(){return Q},BL:function(){return ew},Br:function(){return N},E9:function(){return ep},EG:function(){return ek},EY:function(){return eg},Eb:function(){return E},FC:function(){return q},Gh:function(){return ea},I1:function(){return T},It:function(){return _},J$:function(){return Z},K8:function(){return l},K_:function(){return em},N8:function(){return R},NV:function(){return p},Nc:function(){return er},O3:function(){return ei},OU:function(){return H},Og:function(){return h},Ov:function(){return g},PT:function(){return P},RQ:function(){return k},Rg:function(){return A},So:function(){return V},Vt:function(){return eu},W_:function(){return C},X:function(){return L},XO:function(){return f},Xd:function(){return ee},YU:function(){return ed},Zr:function(){return u},ao:function(){return ef},b1:function(){return z},cu:function(){return ec},eH:function(){return v},fP:function(){return I},g:function(){return eT},hT:function(){return eo},hy:function(){return d},j2:function(){return M},jA:function(){return ey},jE:function(){return el},kK:function(){return w},kn:function(){return O},lg:function(){return et},mR:function(){return U},m_:function(){return F},mp:function(){return eh},n$:function(){return W},o6:function(){return J},pf:function(){return es},qI:function(){return y},qm:function(){return i},rs:function(){return j},s0:function(){return b},tN:function(){return D},um:function(){return en},v9:function(){return Y},wX:function(){return m},wd:function(){return K},xA:function(){return $},zg:function(){return X}});var r=o(58569);console.log=function(){};let a=0,n=e=>new Promise(t=>setTimeout(t,e)),c=async e=>{let t=Date.now();t-a>6e4?(e.includes("Authentication Error - Expired Key")?(r.ZP.info("UI Session Expired. Logging out."),a=t,await n(3e3),document.cookie="token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;",window.location.href="/"):r.ZP.error(e),a=t):console.log("Error suppressed to prevent spam:",e)},s="Authorization";function l(){let e=arguments.length>0&&void 0!==arguments[0]?arguments[0]:"Authorization";console.log("setGlobalLitellmHeaderName: ".concat(e)),s=e}let i=async e=>{try{let t=await fetch("/get/litellm_model_cost_map",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}}),o=await t.json();return console.log("received litellm model cost data: ".concat(o)),o}catch(e){throw console.error("Failed to get model cost map:",e),e}},w=async(e,t)=>{try{let o=await fetch("/model/new",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({...t})});if(!o.ok){let e=await o.text();throw console.error("Error response from the server:",e),Error("Network response was not ok")}let a=await o.json();return console.log("API Response:",a),r.ZP.success("Model created successfully. Wait 60s and refresh on 'All Models' page"),a}catch(e){throw console.error("Failed to create key:",e),e}},d=async e=>{try{let t=await fetch("/model/settings",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok){let e=await t.text();throw c(e),Error("Network response was not ok")}return await t.json()}catch(e){throw console.error("Failed to get callbacks:",e),e}},h=async(e,t)=>{console.log("model_id in model delete call: ".concat(t));try{let o=await fetch("/model/delete",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({id:t})});if(!o.ok){let e=await o.text();throw c(e),console.error("Error response from the server:",e),Error("Network response was not ok")}let a=await o.json();return console.log("API Response:",a),r.ZP.success("Model deleted successfully. Restart server to see this."),a}catch(e){throw console.error("Failed to create key:",e),e}},p=async(e,t)=>{if(console.log("budget_id in budget delete call: ".concat(t)),null!=e)try{let o=await fetch("/budget/delete",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({id:t})});if(!o.ok){let e=await o.text();throw c(e),console.error("Error response from the server:",e),Error("Network response was not ok")}let r=await o.json();return console.log("API Response:",r),r}catch(e){throw console.error("Failed to create key:",e),e}},u=async(e,t)=>{try{console.log("Form Values in budgetCreateCall:",t),console.log("Form Values after check:",t);let o=await fetch("/budget/new",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({...t})});if(!o.ok){let e=await o.text();throw c(e),console.error("Error response from the server:",e),Error("Network response was not ok")}let r=await o.json();return console.log("API Response:",r),r}catch(e){throw console.error("Failed to create key:",e),e}},y=async(e,t)=>{try{console.log("Form Values in budgetUpdateCall:",t),console.log("Form Values after check:",t);let o=await fetch("/budget/update",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({...t})});if(!o.ok){let e=await o.text();throw c(e),console.error("Error response from the server:",e),Error("Network response was not ok")}let r=await o.json();return console.log("API Response:",r),r}catch(e){throw console.error("Failed to create key:",e),e}},f=async(e,t)=>{try{let o=await fetch("/invitation/new",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({user_id:t})});if(!o.ok){let e=await o.text();throw c(e),console.error("Error response from the server:",e),Error("Network response was not ok")}let r=await o.json();return console.log("API Response:",r),r}catch(e){throw console.error("Failed to create key:",e),e}},k=async e=>{try{let t=await fetch("/alerting/settings",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok){let e=await t.text();throw c(e),Error("Network response was not ok")}return await t.json()}catch(e){throw console.error("Failed to get callbacks:",e),e}},m=async(e,t,o)=>{try{if(console.log("Form Values in keyCreateCall:",o),o.description&&(o.metadata||(o.metadata={}),o.metadata.description=o.description,delete o.description,o.metadata=JSON.stringify(o.metadata)),o.metadata){console.log("formValues.metadata:",o.metadata);try{o.metadata=JSON.parse(o.metadata)}catch(e){throw Error("Failed to parse metadata: "+e)}}console.log("Form Values after check:",o);let r=await fetch("/key/generate",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({user_id:t,...o})});if(!r.ok){let e=await r.text();throw c(e),console.error("Error response from the server:",e),Error("Network response was not ok")}let a=await r.json();return console.log("API Response:",a),a}catch(e){throw console.error("Failed to create key:",e),e}},g=async(e,t,o)=>{try{if(console.log("Form Values in keyCreateCall:",o),o.description&&(o.metadata||(o.metadata={}),o.metadata.description=o.description,delete o.description,o.metadata=JSON.stringify(o.metadata)),o.metadata){console.log("formValues.metadata:",o.metadata);try{o.metadata=JSON.parse(o.metadata)}catch(e){throw Error("Failed to parse metadata: "+e)}}console.log("Form Values after check:",o);let r=await fetch("/user/new",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({user_id:t,...o})});if(!r.ok){let e=await r.text();throw c(e),console.error("Error response from the server:",e),Error("Network response was not ok")}let a=await r.json();return console.log("API Response:",a),a}catch(e){throw console.error("Failed to create key:",e),e}},T=async(e,t)=>{try{console.log("in keyDeleteCall:",t);let o=await fetch("/key/delete",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({keys:[t]})});if(!o.ok){let e=await o.text();throw c(e),Error("Network response was not ok")}let r=await o.json();return console.log(r),r}catch(e){throw console.error("Failed to create key:",e),e}},E=async(e,t)=>{try{console.log("in userDeleteCall:",t);let o=await fetch("/user/delete",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({user_ids:t})});if(!o.ok){let e=await o.text();throw c(e),Error("Network response was not ok")}let r=await o.json();return console.log(r),r}catch(e){throw console.error("Failed to delete user(s):",e),e}},j=async(e,t)=>{try{console.log("in teamDeleteCall:",t);let o=await fetch("/team/delete",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({team_ids:[t]})});if(!o.ok){let e=await o.text();throw c(e),Error("Network response was not ok")}let r=await o.json();return console.log(r),r}catch(e){throw console.error("Failed to delete key:",e),e}},N=async function(e,t,o){let r=arguments.length>3&&void 0!==arguments[3]&&arguments[3],a=arguments.length>4?arguments[4]:void 0,n=arguments.length>5?arguments[5]:void 0;try{let l;if(r){l="/user/list";let e=new URLSearchParams;null!=a&&e.append("page",a.toString()),null!=n&&e.append("page_size",n.toString()),l+="?".concat(e.toString())}else l="/user/info","Admin"===o||"Admin Viewer"===o||t&&(l+="?user_id=".concat(t));console.log("Requesting user data from:",l);let i=await fetch(l,{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!i.ok){let e=await i.text();throw c(e),Error("Network response was not ok")}let w=await i.json();return console.log("API Response:",w),w}catch(e){throw console.error("Failed to fetch user data:",e),e}},_=async function(e){let t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:null;try{let o="/team/list";console.log("in teamInfoCall"),t&&(o+="?user_id=".concat(t));let r=await fetch(o,{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!r.ok){let e=await r.text();throw c(e),Error("Network response was not ok")}let a=await r.json();return console.log("/team/list API Response:",a),a}catch(e){throw console.error("Failed to create key:",e),e}},C=async e=>{try{let t="/onboarding/get_token";t+="?invite_link=".concat(e);let o=await fetch(t,{method:"GET",headers:{"Content-Type":"application/json"}});if(!o.ok){let e=await o.text();throw c(e),Error("Network response was not ok")}return await o.json()}catch(e){throw console.error("Failed to create key:",e),e}},F=async(e,t,o,r)=>{try{let a=await fetch("/onboarding/claim_token",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({invitation_link:t,user_id:o,password:r})});if(!a.ok){let e=await a.text();throw c(e),Error("Network response was not ok")}let n=await a.json();return console.log(n),n}catch(e){throw console.error("Failed to delete key:",e),e}},b=async(e,t,o)=>{try{let r=await fetch("/key/".concat(t,"/regenerate"),{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify(o)});if(!r.ok){let e=await r.text();throw c(e),Error("Network response was not ok")}let a=await r.json();return console.log("Regenerate key Response:",a),a}catch(e){throw console.error("Failed to regenerate key:",e),e}},x=!1,S=null,B=async(e,t,o)=>{try{let t=await fetch("/v2/model/info",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok){let e=await t.text();throw e+="error shown=".concat(x),x||(e.includes("No model list passed")&&(e="No Models Exist. Click Add Model to get started."),r.ZP.info(e,10),x=!0,S&&clearTimeout(S),S=setTimeout(()=>{x=!1},1e4)),Error("Network response was not ok")}let o=await t.json();return console.log("modelInfoCall:",o),o}catch(e){throw console.error("Failed to create key:",e),e}},O=async e=>{try{let t=await fetch("/model_group/info",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok)throw await t.text(),Error("Network response was not ok");let o=await t.json();return console.log("modelHubCall:",o),o}catch(e){throw console.error("Failed to create key:",e),e}},P=async e=>{try{let t=await fetch("/get/allowed_ips",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok){let e=await t.text();throw Error("Network response was not ok: ".concat(e))}let o=await t.json();return console.log("getAllowedIPs:",o),o.data}catch(e){throw console.error("Failed to get allowed IPs:",e),e}},v=async(e,t)=>{try{let o=await fetch("/add/allowed_ip",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({ip:t})});if(!o.ok){let e=await o.text();throw Error("Network response was not ok: ".concat(e))}let r=await o.json();return console.log("addAllowedIP:",r),r}catch(e){throw console.error("Failed to add allowed IP:",e),e}},G=async(e,t)=>{try{let o=await fetch("/delete/allowed_ip",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({ip:t})});if(!o.ok){let e=await o.text();throw Error("Network response was not ok: ".concat(e))}let r=await o.json();return console.log("deleteAllowedIP:",r),r}catch(e){throw console.error("Failed to delete allowed IP:",e),e}},J=async(e,t,o,r,a,n,l,i)=>{try{let t="/model/metrics";r&&(t="".concat(t,"?_selected_model_group=").concat(r,"&startTime=").concat(a,"&endTime=").concat(n,"&api_key=").concat(l,"&customer=").concat(i));let o=await fetch(t,{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!o.ok){let e=await o.text();throw c(e),Error("Network response was not ok")}return await o.json()}catch(e){throw console.error("Failed to create key:",e),e}},A=async(e,t,o,r)=>{try{let a="/model/streaming_metrics";t&&(a="".concat(a,"?_selected_model_group=").concat(t,"&startTime=").concat(o,"&endTime=").concat(r));let n=await fetch(a,{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!n.ok){let e=await n.text();throw c(e),Error("Network response was not ok")}return await n.json()}catch(e){throw console.error("Failed to create key:",e),e}},I=async(e,t,o,r,a,n,l,i)=>{try{let t="/model/metrics/slow_responses";r&&(t="".concat(t,"?_selected_model_group=").concat(r,"&startTime=").concat(a,"&endTime=").concat(n,"&api_key=").concat(l,"&customer=").concat(i));let o=await fetch(t,{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!o.ok){let e=await o.text();throw c(e),Error("Network response was not ok")}return await o.json()}catch(e){throw console.error("Failed to create key:",e),e}},R=async(e,t,o,r,a,n,l,i)=>{try{let t="/model/metrics/exceptions";r&&(t="".concat(t,"?_selected_model_group=").concat(r,"&startTime=").concat(a,"&endTime=").concat(n,"&api_key=").concat(l,"&customer=").concat(i));let o=await fetch(t,{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!o.ok){let e=await o.text();throw c(e),Error("Network response was not ok")}return await o.json()}catch(e){throw console.error("Failed to create key:",e),e}},V=async(e,t,o)=>{console.log("in /models calls, globalLitellmHeaderName",s);try{let t=await fetch("/models",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok){let e=await t.text();throw c(e),Error("Network response was not ok")}return await t.json()}catch(e){throw console.error("Failed to create key:",e),e}},U=async e=>{try{let t="/global/spend/teams";console.log("in teamSpendLogsCall:",t);let o=await fetch("".concat(t),{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!o.ok){let e=await o.text();throw c(e),Error("Network response was not ok")}let r=await o.json();return console.log(r),r}catch(e){throw console.error("Failed to create key:",e),e}},Z=async(e,t,o,r)=>{try{let a="/global/spend/tags";t&&o&&(a="".concat(a,"?start_date=").concat(t,"&end_date=").concat(o)),r&&(a+="".concat(a,"&tags=").concat(r.join(","))),console.log("in tagsSpendLogsCall:",a);let n=await fetch("".concat(a),{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!n.ok)throw await n.text(),Error("Network response was not ok");let c=await n.json();return console.log(c),c}catch(e){throw console.error("Failed to create key:",e),e}},L=async e=>{try{let t="/global/spend/all_tag_names";console.log("in global/spend/all_tag_names call",t);let o=await fetch("".concat(t),{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!o.ok)throw await o.text(),Error("Network response was not ok");let r=await o.json();return console.log(r),r}catch(e){throw console.error("Failed to create key:",e),e}},M=async e=>{try{let t="/global/all_end_users";console.log("in global/all_end_users call",t);let o=await fetch("".concat(t),{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!o.ok)throw await o.text(),Error("Network response was not ok");let r=await o.json();return console.log(r),r}catch(e){throw console.error("Failed to create key:",e),e}},q=async e=>{try{let t=await fetch("/global/spend/logs",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok){let e=await t.text();throw c(e),Error("Network response was not ok")}let o=await t.json();return console.log(o),o}catch(e){throw console.error("Failed to create key:",e),e}},D=async e=>{try{let t=await fetch("/global/spend/keys?limit=5",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok){let e=await t.text();throw c(e),Error("Network response was not ok")}let o=await t.json();return console.log(o),o}catch(e){throw console.error("Failed to create key:",e),e}},z=async(e,t,o,r)=>{try{let a="";a=t?JSON.stringify({api_key:t,startTime:o,endTime:r}):JSON.stringify({startTime:o,endTime:r});let n={method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:a},l=await fetch("/global/spend/end_users",n);if(!l.ok){let e=await l.text();throw c(e),Error("Network response was not ok")}let i=await l.json();return console.log(i),i}catch(e){throw console.error("Failed to create key:",e),e}},H=async(e,t,o,r)=>{try{let a="/global/spend/provider";o&&r&&(a+="?start_date=".concat(o,"&end_date=").concat(r)),t&&(a+="&api_key=".concat(t));let n={method:"GET",headers:{[s]:"Bearer ".concat(e)}},l=await fetch(a,n);if(!l.ok){let e=await l.text();throw c(e),Error("Network response was not ok")}let i=await l.json();return console.log(i),i}catch(e){throw console.error("Failed to fetch spend data:",e),e}},K=async(e,t,o)=>{try{let r="/global/activity";t&&o&&(r+="?start_date=".concat(t,"&end_date=").concat(o));let a={method:"GET",headers:{[s]:"Bearer ".concat(e)}},n=await fetch(r,a);if(!n.ok)throw await n.text(),Error("Network response was not ok");let c=await n.json();return console.log(c),c}catch(e){throw console.error("Failed to fetch spend data:",e),e}},X=async(e,t,o)=>{try{let r="/global/activity/cache_hits";t&&o&&(r+="?start_date=".concat(t,"&end_date=").concat(o));let a={method:"GET",headers:{[s]:"Bearer ".concat(e)}},n=await fetch(r,a);if(!n.ok)throw await n.text(),Error("Network response was not ok");let c=await n.json();return console.log(c),c}catch(e){throw console.error("Failed to fetch spend data:",e),e}},$=async(e,t,o)=>{try{let r="/global/activity/model";t&&o&&(r+="?start_date=".concat(t,"&end_date=").concat(o));let a={method:"GET",headers:{[s]:"Bearer ".concat(e)}},n=await fetch(r,a);if(!n.ok)throw await n.text(),Error("Network response was not ok");let c=await n.json();return console.log(c),c}catch(e){throw console.error("Failed to fetch spend data:",e),e}},W=async(e,t,o,r)=>{try{let a="/global/activity/exceptions";t&&o&&(a+="?start_date=".concat(t,"&end_date=").concat(o)),r&&(a+="&model_group=".concat(r));let n={method:"GET",headers:{[s]:"Bearer ".concat(e)}},c=await fetch(a,n);if(!c.ok)throw await c.text(),Error("Network response was not ok");let l=await c.json();return console.log(l),l}catch(e){throw console.error("Failed to fetch spend data:",e),e}},Y=async(e,t,o,r)=>{try{let a="/global/activity/exceptions/deployment";t&&o&&(a+="?start_date=".concat(t,"&end_date=").concat(o)),r&&(a+="&model_group=".concat(r));let n={method:"GET",headers:{[s]:"Bearer ".concat(e)}},c=await fetch(a,n);if(!c.ok)throw await c.text(),Error("Network response was not ok");let l=await c.json();return console.log(l),l}catch(e){throw console.error("Failed to fetch spend data:",e),e}},Q=async e=>{try{let t=await fetch("/global/spend/models?limit=5",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok){let e=await t.text();throw c(e),Error("Network response was not ok")}let o=await t.json();return console.log(o),o}catch(e){throw console.error("Failed to create key:",e),e}},ee=async(e,t)=>{try{let o="/user/get_users?role=".concat(t);console.log("in userGetAllUsersCall:",o);let r=await fetch(o,{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!r.ok){let e=await r.text();throw c(e),Error("Network response was not ok")}let a=await r.json();return console.log(a),a}catch(e){throw console.error("Failed to get requested models:",e),e}},et=async e=>{try{let t=await fetch("/user/available_roles",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok)throw await t.text(),Error("Network response was not ok");let o=await t.json();return console.log("response from user/available_role",o),o}catch(e){throw e}},eo=async(e,t)=>{try{console.log("Form Values in teamCreateCall:",t);let o=await fetch("/team/new",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({...t})});if(!o.ok){let e=await o.text();throw c(e),console.error("Error response from the server:",e),Error("Network response was not ok")}let r=await o.json();return console.log("API Response:",r),r}catch(e){throw console.error("Failed to create key:",e),e}},er=async(e,t)=>{try{console.log("Form Values in keyUpdateCall:",t);let o=await fetch("/key/update",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({...t})});if(!o.ok){let e=await o.text();throw c(e),console.error("Error response from the server:",e),Error("Network response was not ok")}let r=await o.json();return console.log("Update key Response:",r),r}catch(e){throw console.error("Failed to create key:",e),e}},ea=async(e,t)=>{try{console.log("Form Values in teamUpateCall:",t);let o=await fetch("/team/update",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({...t})});if(!o.ok){let e=await o.text();throw c(e),console.error("Error response from the server:",e),Error("Network response was not ok")}let r=await o.json();return console.log("Update Team Response:",r),r}catch(e){throw console.error("Failed to create key:",e),e}},en=async(e,t)=>{try{console.log("Form Values in modelUpateCall:",t);let o=await fetch("/model/update",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({...t})});if(!o.ok){let e=await o.text();throw c(e),console.error("Error update from the server:",e),Error("Network response was not ok")}let r=await o.json();return console.log("Update model Response:",r),r}catch(e){throw console.error("Failed to update model:",e),e}},ec=async(e,t,o)=>{try{console.log("Form Values in teamMemberAddCall:",o);let r=await fetch("/team/member_add",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({team_id:t,member:o})});if(!r.ok){let e=await r.text();throw c(e),console.error("Error response from the server:",e),Error("Network response was not ok")}let a=await r.json();return console.log("API Response:",a),a}catch(e){throw console.error("Failed to create key:",e),e}},es=async(e,t,o)=>{try{console.log("Form Values in userUpdateUserCall:",t);let r={...t};null!==o&&(r.user_role=o),r=JSON.stringify(r);let a=await fetch("/user/update",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:r});if(!a.ok){let e=await a.text();throw c(e),console.error("Error response from the server:",e),Error("Network response was not ok")}let n=await a.json();return console.log("API Response:",n),n}catch(e){throw console.error("Failed to create key:",e),e}},el=async(e,t)=>{try{let o="/health/services?service=".concat(t);console.log("Checking Slack Budget Alerts service health");let a=await fetch(o,{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!a.ok){let e=await a.text();throw c(e),Error(e)}let n=await a.json();return r.ZP.success("Test request to ".concat(t," made - check logs/alerts on ").concat(t," to verify")),n}catch(e){throw console.error("Failed to perform health check:",e),e}},ei=async e=>{try{let t=await fetch("/budget/list",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok){let e=await t.text();throw c(e),Error("Network response was not ok")}return await t.json()}catch(e){throw console.error("Failed to get callbacks:",e),e}},ew=async(e,t,o)=>{try{let t=await fetch("/get/config/callbacks",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok){let e=await t.text();throw c(e),Error("Network response was not ok")}return await t.json()}catch(e){throw console.error("Failed to get callbacks:",e),e}},ed=async e=>{try{let t=await fetch("/config/list?config_type=general_settings",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok){let e=await t.text();throw c(e),Error("Network response was not ok")}return await t.json()}catch(e){throw console.error("Failed to get callbacks:",e),e}},eh=async e=>{try{let t=await fetch("/config/pass_through_endpoint",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok){let e=await t.text();throw c(e),Error("Network response was not ok")}return await t.json()}catch(e){throw console.error("Failed to get callbacks:",e),e}},ep=async(e,t)=>{try{let o=await fetch("/config/field/info?field_name=".concat(t),{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!o.ok)throw await o.text(),Error("Network response was not ok");return await o.json()}catch(e){throw console.error("Failed to set callbacks:",e),e}},eu=async(e,t)=>{try{let o=await fetch("/config/pass_through_endpoint",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({...t})});if(!o.ok){let e=await o.text();throw c(e),Error("Network response was not ok")}return await o.json()}catch(e){throw console.error("Failed to set callbacks:",e),e}},ey=async(e,t,o)=>{try{let a=await fetch("/config/field/update",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({field_name:t,field_value:o,config_type:"general_settings"})});if(!a.ok){let e=await a.text();throw c(e),Error("Network response was not ok")}let n=await a.json();return r.ZP.success("Successfully updated value!"),n}catch(e){throw console.error("Failed to set callbacks:",e),e}},ef=async(e,t)=>{try{let o=await fetch("/config/field/delete",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({field_name:t,config_type:"general_settings"})});if(!o.ok){let e=await o.text();throw c(e),Error("Network response was not ok")}let a=await o.json();return r.ZP.success("Field reset on proxy"),a}catch(e){throw console.error("Failed to get callbacks:",e),e}},ek=async(e,t)=>{try{let o=await fetch("/config/pass_through_endpoint".concat(t),{method:"DELETE",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!o.ok){let e=await o.text();throw c(e),Error("Network response was not ok")}return await o.json()}catch(e){throw console.error("Failed to get callbacks:",e),e}},em=async(e,t)=>{try{let o=await fetch("/config/update",{method:"POST",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"},body:JSON.stringify({...t})});if(!o.ok){let e=await o.text();throw c(e),Error("Network response was not ok")}return await o.json()}catch(e){throw console.error("Failed to set callbacks:",e),e}},eg=async e=>{try{let t=await fetch("/health",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok){let e=await t.text();throw c(e),Error("Network response was not ok")}return await t.json()}catch(e){throw console.error("Failed to call /health:",e),e}},eT=async e=>{try{let t=await fetch("/sso/get/ui_settings",{method:"GET",headers:{[s]:"Bearer ".concat(e),"Content-Type":"application/json"}});if(!t.ok)throw await t.text(),Error("Network response was not ok");return await t.json()}catch(e){throw console.error("Failed to get callbacks:",e),e}}}}]);