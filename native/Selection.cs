using System;
using System.Text;
using System.Windows.Automation;
class Selection {
 [STAThread] static void Main() {
  Console.OutputEncoding=new UTF8Encoding(false);
  try {
   AutomationElement element=AutomationElement.FocusedElement;
   if(element==null || element.Current.IsPassword) return;
   for(int depth=0; element!=null && depth<7; depth++) {
    object pattern;
    if(element.TryGetCurrentPattern(TextPattern.Pattern,out pattern)) {
     var ranges=((TextPattern)pattern).GetSelection();
     var result=new StringBuilder();
     foreach(var range in ranges) { var text=range.GetText(30000); if(!String.IsNullOrWhiteSpace(text)) result.AppendLine(text); }
     if(result.Length>0) { Console.Write(result.ToString()); return; }
    }
    element=TreeWalker.ControlViewWalker.GetParent(element);
   }
  } catch { }
 }
}
