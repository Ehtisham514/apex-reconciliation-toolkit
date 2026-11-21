"use strict";
const fs=require("node:fs"),path=require("node:path");
const {readInputs}=require("./run.js"),{filings,anchors}=readInputs();
const safe=JSON.stringify({...filings,anchors}).replace(/</g,"\\u003c");
const read=k=>fs.readFileSync(path.join(__dirname,k),"utf8");
const html=read("workbench.template.html").replace("__BANK_SNAPSHOT__",()=>safe).replace("__BANK_ENGINE__",()=>read("engine.js"));
fs.writeFileSync(path.join(__dirname,"index.html"),html);
