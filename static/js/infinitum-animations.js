
/* Infinitum — performance mode */
const rafScheduler=(()=>{const p=new Set();let r=null;function f(){r=null;p.forEach(fn=>{p.delete(fn);fn();});}return fn=>{p.add(fn);if(!r)r=requestAnimationFrame(f);};})();
const progressBar=document.getElementById('progress-bar');
const nav=document.getElementById('main-nav');
let lastScrollY=-1;
function handleScroll(){const sy=window.scrollY;if(sy===lastScrollY)return;lastScrollY=sy;if(progressBar){const denom=Math.max(1,document.body.scrollHeight-window.innerHeight);progressBar.style.transform=`scaleX(${Math.min(sy/denom,1)})`;}if(nav)nav.classList.toggle('scrolled',sy>50);}
window.addEventListener('scroll',()=>rafScheduler(handleScroll),{passive:true});handleScroll();
const revealObs=new IntersectionObserver((entries)=>{entries.forEach((entry,i)=>{if(entry.isIntersecting){entry.target.style.transitionDelay=(i*50)+'ms';entry.target.classList.add('visible');revealObs.unobserve(entry.target);}});},{threshold:.08,rootMargin:'0px 0px -40px 0px'});
document.querySelectorAll('.reveal').forEach(el=>revealObs.observe(el));
function animCounter(el){const target=parseInt(el.dataset.target||'0',10);const suffix=el.dataset.suffix||'';const start=performance.now();const dur=1400;const isK=target>=1000;function update(now){const p=Math.min((now-start)/dur,1);const val=Math.round((1-Math.pow(1-p,4))*target);el.textContent=isK?Math.floor(val/1000)+'K'+suffix:val+suffix;if(p<1)requestAnimationFrame(update);}requestAnimationFrame(update);}
const cntObs=new IntersectionObserver((entries)=>{entries.forEach(entry=>{if(entry.isIntersecting&&!entry.target.dataset.counted){entry.target.dataset.counted='1';animCounter(entry.target);cntObs.unobserve(entry.target);}});},{threshold:.5});
document.querySelectorAll('.stat-number[data-target]').forEach(el=>cntObs.observe(el));
const heroTitle=document.querySelector('.hero-title');
if(heroTitle&&matchMedia('(min-width:901px) and (prefers-reduced-motion:no-preference)').matches){function triggerGlitch(){heroTitle.classList.add('glitch');setTimeout(()=>heroTitle.classList.remove('glitch'),300);setTimeout(triggerGlitch,7000+Math.random()*6000);}setTimeout(triggerGlitch,3500);}
if(matchMedia('(hover:hover) and (pointer:fine) and (min-width:901px)').matches){
 document.querySelectorAll('.tilt-card').forEach(card=>{let pending=false,rect=null;card.addEventListener('mouseenter',()=>{rect=card.getBoundingClientRect();},{passive:true});card.addEventListener('mousemove',e=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;if(!rect)return;const x=(e.clientX-rect.left)/rect.width-.5;const y=(e.clientY-rect.top)/rect.height-.5;card.style.transform=`perspective(700px) rotateY(${x*10}deg) rotateX(${-y*10}deg) scale(1.02)`;});},{passive:true});card.addEventListener('mouseleave',()=>{rect=null;card.style.transform='perspective(700px) rotateY(0) rotateX(0) scale(1)';},{passive:true});});
 document.querySelectorAll('.magnetic').forEach(btn=>{let pending=false,rect=null;btn.addEventListener('mouseenter',()=>{rect=btn.getBoundingClientRect();},{passive:true});btn.addEventListener('mousemove',e=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;if(!rect)return;const x=(e.clientX-rect.left-rect.width/2)*.22;const y=(e.clientY-rect.top-rect.height/2)*.22;btn.style.transform=`translate(${x}px,${y}px)`;});},{passive:true});btn.addEventListener('mouseleave',()=>{rect=null;btn.style.transform='translate(0,0)';},{passive:true});});
}



/* Integrated artistic direction — performance safe */
const brandTimeline = document.querySelector('.timeline');
function updateBrandTimeline() {
  if (!brandTimeline) return;
  const rect = brandTimeline.getBoundingClientRect();
  const vh = window.innerHeight || document.documentElement.clientHeight;
  const total = Math.max(1, rect.height + vh * 0.6);
  const passed = vh * 0.72 - rect.top;
  const progress = Math.min(Math.max(passed / total, 0), 1);
  brandTimeline.style.setProperty('--timeline-progress', progress.toFixed(3));
}
if (brandTimeline) {
  window.addEventListener('scroll', () => rafScheduler(updateBrandTimeline), { passive: true });
  window.addEventListener('resize', () => rafScheduler(updateBrandTimeline), { passive: true });
  updateBrandTimeline();
}
