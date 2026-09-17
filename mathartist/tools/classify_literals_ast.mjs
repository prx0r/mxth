#!/usr/bin/env node
import fs from "node:fs";
import crypto from "node:crypto";
import { parse } from "acorn";
import * as loose from "acorn-loose";
import * as walk from "acorn-walk";

const file=process.argv[2];
if(!file){console.error("usage: classify_literals_ast.mjs <sketch.js>");process.exit(2)}
const code=fs.readFileSync(file,"utf8");
const opts={ecmaVersion:"latest",sourceType:"script",locations:true,ranges:true,allowHashBang:true,allowReturnOutsideFunction:true};
let ast,parser="acorn",parse_warning=null;
try{ast=parse(code,opts)}catch(e){ast=loose.parse(code,opts);parser="acorn-loose";parse_warning=e.message}

function calleeName(n){
  if(!n)return "";
  if(n.type==="Identifier")return n.name;
  if(n.type==="MemberExpression"){
    const a=calleeName(n.object),b=n.computed?"":calleeName(n.property);
    return a&&b?`${a}.${b}`:(b||a);
  }
  return "";
}
function contains(a,n){return !!a && a.start<=n.start && a.end>=n.end}
function nearest(ancestors,type){
  for(let i=ancestors.length-2;i>=0;i--)if(ancestors[i]?.type===type)return ancestors[i];
  return null;
}
const runtime=new Set(["createCanvas","resizeCanvas","pixelDensity","frameRate","smooth","noSmooth"]);
const color=new Set(["background","fill","stroke","color","tint","colorMode","strokeWeight"]);
const geom=new Set(["point","vertex","curveVertex","bezierVertex","line","circle","ellipse","rect","translate","rotate","scale"]);
const trig=new Set(["sin","cos","tan","asin","acos","atan","atan2"]);
const stochastic=new Set(["noise","random","randomGaussian"]);
const results=[];

walk.ancestor(ast,{
  Literal(node,state,ancestors){
    if(typeof node.value!=="number")return;
    const parent=ancestors.at(-2);
    const call=[...ancestors].reverse().find(a=>a?.type==="CallExpression"&&contains(a,node));
    const callName=calleeName(call?.callee).split(".").at(-1);
    const forNode=nearest(ancestors,"ForStatement");
    const ifNode=nearest(ancestors,"IfStatement");
    const condNode=nearest(ancestors,"ConditionalExpression");
    const assign=nearest(ancestors,"AssignmentExpression");
    const binary=nearest(ancestors,"BinaryExpression");
    let role="UNKNOWN",confidence=.35,mutable=true,why="numeric AST literal";

    if(runtime.has(callName)){role="FIXED_RUNTIME";confidence=.99;mutable=false;why=`argument of ${callName}()`}
    else if(color.has(callName)){role="COLOR_ALPHA";confidence=.98;mutable=false;why=`argument of ${callName}()`}
    else if(parent?.type==="MemberExpression"&&parent.computed&&parent.property===node){role="STRUCTURAL_INDEX";confidence=.95;mutable=false;why="computed member index"}
    else if(forNode&&(contains(forNode.test,node)||contains(forNode.update,node))){role="SAMPLING_BUDGET";confidence=.9;mutable=false;why="for-loop limit/update"}
    else if(assign&&assign.left?.type==="Identifier"&&/^(t|time|phase|angle|step)$/i.test(assign.left.name)){role="INITIAL_CONDITION";confidence=.9;mutable=true;why=`state assignment to ${assign.left.name}`}
    else if(parent?.type==="AssignmentExpression"&&parent.operator!=="="){role="TIME_STEP";confidence=.7;mutable=true;why=`compound assignment ${parent.operator}`}
    else if(binary?.operator==="**"&&contains(binary.right,node)){role="EXPONENT";confidence=.95;mutable=true;why="exponent RHS"}
    else if((ifNode&&contains(ifNode.test,node))||(condNode&&contains(condNode.test,node))){role="BRANCH_SELECTOR";confidence=.8;mutable=true;why="conditional threshold"}
    else if(trig.has(callName)){role="MATHEMATICAL_COEFFICIENT";confidence=.85;mutable=true;why=`inside ${callName}()`}
    else if(stochastic.has(callName)){role="STOCHASTIC_PARAMETER";confidence=.8;mutable=true;why=`inside ${callName}()`}
    else if(geom.has(callName)){role="MATHEMATICAL_COEFFICIENT";confidence=.65;mutable=true;why=`feeds ${callName}()`}
    else if(binary&&["+","-","*","/","%","**"].includes(binary.operator)){role=binary.operator==="%"?"BRANCH_SELECTOR":"MATHEMATICAL_COEFFICIENT";confidence=.6;mutable=true;why=`arithmetic ${binary.operator}`}

    let start=node.start,end=node.end,value=node.value;
    if(parent?.type==="UnaryExpression"&&parent.operator==="-"&&parent.argument===node){
      start=parent.start;end=parent.end;value=-node.value;
    }
    results.push({
      literal:code.slice(start,end),value,role,mutable_art_program:mutable,confidence,why,start,end,
      line:node.loc?.start.line,column:node.loc?.start.column,call:callName||null
    });
  }
});
console.log(JSON.stringify({
  file,code_sha256:crypto.createHash("sha256").update(code).digest("hex"),
  parser,parse_warning,total_numeric_literals:results.length,
  mutation_candidates:results.filter(x=>x.mutable_art_program).length,
  candidates:results.filter(x=>x.mutable_art_program),all_literals:results
},null,2));
