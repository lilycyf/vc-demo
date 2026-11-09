"""Actual shared entrypoint for a researcher-operated, task-neutral closed loop."""
import argparse
import json
from pathlib import Path
from .session import Session


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-dir',type=Path,required=True)
    commands=p.add_subparsers(dest='action',required=True)
    init=commands.add_parser('init');init.add_argument('--spec',type=Path,required=True)
    commands.add_parser('context');commands.add_parser('select');commands.add_parser('report')
    submit=commands.add_parser('propose');submit.add_argument('--file',type=Path,required=True)
    rerank=commands.add_parser('rerank');rerank.add_argument('--file',type=Path,required=True)
    exhaustion=commands.add_parser('exhaustion');exhaustion.add_argument('--file',type=Path,required=True)
    seal=commands.add_parser('seal');seal.add_argument('--node',required=True);seal.add_argument('--file',type=Path,required=True)
    execute=commands.add_parser('execute');execute.add_argument('--node',required=True)
    skip=commands.add_parser('skip');skip.add_argument('--node',required=True);skip.add_argument('--file',type=Path,required=True)
    control=commands.add_parser('control');control.add_argument('--file',type=Path,required=True)
    freeze=commands.add_parser('freeze');freeze.add_argument('--nodes',nargs='+',required=True)
    confirm=commands.add_parser('confirm');confirm.add_argument('--node',required=True)
    analyze=commands.add_parser('analyze');analyze.add_argument('--node',required=True);analyze.add_argument('--analysis',required=True)
    plan=commands.add_parser('plan-analysis');plan.add_argument('--id',required=True);plan.add_argument('--file',type=Path,required=True)
    a=p.parse_args(argv);session=Session(a.run_dir)
    if a.action=='init':
        session=Session.initialize(a.run_dir,json.loads(a.spec.read_text()));result=session.context()
    elif a.action=='context':result=session.context()
    elif a.action=='propose':result={'accepted':session.propose(json.loads(a.file.read_text()))}
    elif a.action=='rerank':
        value=json.loads(a.file.read_text());session.rerank(value['updates'],value['evidence_id']);result=session.context()
    elif a.action=='exhaustion':
        value=json.loads(a.file.read_text());session.declare_exhaustion(value['reason'],value['attempts']);result=session.context()
    elif a.action=='select':result=session.select()
    elif a.action=='seal':
        value=json.loads(a.file.read_text());result=session.seal(a.node,value['execution'],value['recipe'])
    elif a.action=='execute':
        receipt=session.execute(a.node)
        result={k:v for k,v in receipt.items() if k not in {'prediction_table','fit_audit','composition_audit'}}
    elif a.action=='skip':
        value=json.loads(a.file.read_text());session.skip(a.node,value['reason'],value['attempts']);result=session.context()
    elif a.action=='control':result=session.record_control(**json.loads(a.file.read_text()))
    elif a.action=='freeze':result=session.freeze(a.nodes)
    elif a.action=='confirm':result=session.confirm(a.node)
    elif a.action=='analyze':result=session.analyze(a.node,a.analysis)
    elif a.action=='plan-analysis':
        value=json.loads(a.file.read_text());result=session.plan_analysis(a.id,**value)
    else:result=session.verdict()
    print(json.dumps(result,indent=2,sort_keys=True))


if __name__=='__main__':main()
