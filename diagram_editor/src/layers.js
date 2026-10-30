// 레이어(포토샵처럼): 문서의 개체를 겹(레이어)으로 나눠 보이기·잠그기·순서를 따로 정한다.
// graph.layers는 아래→위 순서의 [{id,name,visible,locked}], 개체는 data.layer로 자기 레이어를 가리킨다.
// 그림판 배경 사진은 레이어 밖에서 늘 맨 뒤에 있다.
export const DEFAULT_LAYER_ID='layer-1';
export const MAX_LAYERS=50;
const LAYER_STEP=10;

export const defaultLayers=()=>[{id:DEFAULT_LAYER_ID,name:'레이어 1',visible:true,locked:false}];

/** 저장된 레이어 목록을 검사해 고친다(비거나 잘못되면 기본 레이어 하나). */
export function validateLayers(value){
 if(value==null)return defaultLayers();
 if(!Array.isArray(value)||value.length>MAX_LAYERS)throw new Error('레이어 데이터가 올바르지 않습니다.');
 const ids=new Set();
 const layers=value.map(l=>{
  if(typeof l?.id!=='string'||!/^[A-Za-z0-9_-]{1,64}$/.test(l.id)||ids.has(l.id))throw new Error('레이어 데이터가 올바르지 않습니다.');
  if(typeof l.name!=='string'||l.name.length>60)throw new Error('레이어 이름이 올바르지 않습니다.');
  ids.add(l.id);
  return {id:l.id,name:l.name.trim()||'레이어',visible:l.visible!==false,locked:l.locked===true};
 });
 return layers.length?layers:defaultLayers();
}

/** 레이어가 없거나 사라진 레이어를 가리키는 개체는 맨 아래 레이어로 보낸다. */
export function layerOf(node,layers){
 const wanted=node?.data?.layer;
 return layers.some(l=>l.id===wanted)?wanted:layers[0].id;
}

/** 위에 새 레이어를 넣는다. 이름은 '레이어 N'(겹치지 않는 가장 작은 N). */
export function addLayer(layers,identity=crypto.randomUUID().replace(/-/g,'').slice(0,16)){
 if(layers.length>=MAX_LAYERS)throw new Error('레이어는 '+MAX_LAYERS+'개까지 만들 수 있습니다.');
 const names=new Set(layers.map(l=>l.name));
 let n=layers.length+1;while(names.has('레이어 '+n))n++;
 return [...layers,{id:'layer-'+identity,name:'레이어 '+n,visible:true,locked:false}];
}

export const updateLayer=(layers,layerId,patch)=>layers.map(l=>l.id===layerId?{...l,...patch}:l);

/** 레이어를 한 칸 위(+1)나 아래(-1)로. */
export function moveLayer(layers,layerId,step){
 const i=layers.findIndex(l=>l.id===layerId),j=i+step;
 if(i<0||j<0||j>=layers.length)return layers;
 const next=[...layers];[next[i],next[j]]=[next[j],next[i]];return next;
}

/** 레이어와 그 안의 개체(이어진 연결선 포함)를 지운다. 마지막 레이어는 지우지 않는다. */
export function removeLayer(graph,layerId){
 const layers=graph.layers??defaultLayers();
 if(layers.length<=1||!layers.some(l=>l.id===layerId))return graph;
 const gone=new Set(graph.nodes.filter(n=>!n.data?.background&&layerOf(n,layers)===layerId).map(n=>n.id));
 return {...graph,layers:layers.filter(l=>l.id!==layerId),
  nodes:graph.nodes.filter(n=>!gone.has(n.id)),edges:graph.edges.filter(e=>!gone.has(e.source)&&!gone.has(e.target))};
}

/** 고른 개체를 다른 레이어로 옮긴다. */
export function assignLayer(nodes,ids,layerId){
 const chosen=new Set(ids);
 return nodes.map(n=>chosen.has(n.id)&&!n.data?.background?{...n,data:{...n.data,layer:layerId}}:n);
}

/** 화면에 넘길 개체: 숨긴 레이어는 감추고, 잠근 레이어는 고르거나 끌 수 없게, 쌓는 순서는 레이어 순서대로. */
export function layeredNodes(nodes,layers){
 if(!layers?.length)return nodes;
 const index=new Map(layers.map((l,i)=>[l.id,i]));
 return nodes.map(n=>{
  if(n.data?.background)return n;
  const layer=layers[index.get(layerOf(n,layers))];
  const z=index.get(layer.id)*LAYER_STEP+(n.selected?1:0);
  let shown=n.zIndex===z?n:{...n,zIndex:z};
  if(!layer.visible)shown={...shown,hidden:true,selected:false};
  if(layer.locked)shown={...shown,draggable:false,selectable:false,connectable:false,deletable:false,selected:false};
  return shown;
 });
}

/** 숨긴 레이어의 개체와 거기에 이어진 연결선을 화면에서 감춘다. */
export function layeredEdges(edges,nodes,layers){
 if(!layers?.length)return edges;
 const hidden=new Set(nodes.filter(n=>!n.data?.background&&layers.find(l=>l.id===layerOf(n,layers))?.visible===false).map(n=>n.id));
 if(!hidden.size)return edges;
 return edges.map(e=>hidden.has(e.source)||hidden.has(e.target)?{...e,hidden:true}:e);
}

/** 내보내기·그림 복사용: 숨긴 레이어를 빼고 레이어 순서(아래→위)로 개체를 줄 세운다. */
export function visibleGraph(graph){
 const layers=graph.layers;
 if(!layers?.length)return graph;
 const order=new Map(layers.map((l,i)=>[l.id,i]));
 const background=graph.nodes.filter(n=>n.data?.background);
 const shown=graph.nodes.filter(n=>!n.data?.background&&layers[order.get(layerOf(n,layers))].visible);
 shown.sort((a,b)=>order.get(layerOf(a,layers))-order.get(layerOf(b,layers)));
 const ids=new Set([...background,...shown].map(n=>n.id));
 return {...graph,nodes:[...background,...shown],edges:graph.edges.filter(e=>ids.has(e.source)&&ids.has(e.target))};
}

/** 잠근 레이어 개체는 지우기에서 뺀다. */
export const unlockedIds=(nodes,layers)=>new Set(nodes.filter(n=>!n.data?.background&&!(layers??[]).find(l=>l.id===layerOf(n,layers))?.locked).map(n=>n.id));
