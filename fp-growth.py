import argparse
import operator

SUBSET_DISCARD_RATE = 0.8
SUPERSET_DISCARD_RATE = 0.1
class TreeNode:
  parent = None
  copyMark = False

  def __init__(self, name, value):
     self.name = name
     self.value = value
     self.children = []

  def insertChild(self, child):
     self.children.append(child)
     child.parent = self

# used to copy subtree
def copyNode(node, newItem2Ref):
   if not node.copyMark:
     return None
   node.copyMark = False
   newNode = TreeNode(node.name, node.value)
   newNode.copyMark = True
   if node.name != "":
      if node.name in newItem2Ref:
         newItem2Ref[node.name].append(newNode)
      else:
         newItem2Ref[node.name] = [newNode]
   for child in node.children:
       nc = copyNode(child, newItem2Ref)
       if nc is not None:
         newNode.insertChild(nc)
   return newNode

# used to print tree 
def printTree(root):
   if root is not None:
      print "start"
      oneLevelInTree = [root]
      printLevel(oneLevelInTree)
      print "end"

# used to print tree
def printLevel(oneLevel):
   lowerLevel = []
   for node in oneLevel:
      print node.name, "-", node.value, "-", node.copyMark
      lowerLevel.extend(node.children)
   print 20*'-'
   if len(lowerLevel) > 0:
      printLevel(lowerLevel)

# used for construct FP-tree, insert one sentence(sequence of elements)
# item: one sentence
# root: tree root node
# dictionary: [element]->[priority]
# item2Ref: [element]->[nodes in tree]
def createBranchUnderRoot(item, root, dictionary, item2Ref):
  curNode = root
  sequence={}
  for c in item.strip().split(' '):
     if c != ' ' and c != '' and c!='{' and c!='}' and c!='>' and c!='--':
        sequence[c]=dictionary[c]
  sorted_x = sorted(sequence.iteritems(), key=operator.itemgetter(1),reverse =True)
  for c in sorted_x:
     element=c[0]
     #print character
     findMatchC=False
     for child in curNode.children:
        if child.name == element: 
           #print 'find match child'
           child.value += 1
           curNode = child
           findMatchC = True
     if not findMatchC:
        #print 'add child to %s'%(curNode.name)
        newChild = TreeNode(element, 1)
        if element in item2Ref:
           item2Ref[element].append(newChild)
        else:
           item2Ref[element] = [newChild]
        curNode.insertChild(newChild)
        curNode = newChild

# Insert all sentences in fp-tree      
def createTree(sentences, root, dictionary, item2Ref):
  for sentence in sentences:
     createBranchUnderRoot(sentence, root, dictionary, item2Ref)

# update node value by cumulate children's value
def updateNodeValue(root):
   root.copyMark = False
   if len(root.children) == 0:
      return root.value
   value = 0
   for child in root.children:
     value += updateNodeValue(child)
   root.value = value
   return value

# copy subtree out and update values for new subtree
def copyAndUpdateTree(root, item, item2ref, prefix):
   # mark all paths need to copy
   nodelist = item2ref[item]
   for startnode in nodelist:
     node = startnode
     node.copyMark = True
     while node.parent is not None:
        node.parent.copyMark = True
        node = node.parent

   # copy new sub-tree, new ref, clear old tree copyMark
   newItem2Ref={}
   newRoot = copyNode(root, newItem2Ref)

   # update new tree value, clear copyMark
   newNodeList = newItem2Ref[item]
   updateNodeValue(newRoot)
  
   # del all nodes of current item from new subtree
   del newItem2Ref[item]
  
   # return sub-tree and new reference list
   return newRoot, newItem2Ref

def isSubset(lista,listb):
   passed = True
   for word in lista:
     if word not in listb:
        passed = False
        break;
   return passed

def discardItem(prefixDic, name, value):
   deleteList = []
   add = True
   newSeq= name.strip().split(' ')
   if len(newSeq)<3:
      return 
   for item in prefixDic.keys():
      bset = item.strip().split(' ')
      if len(bset) != len(newSeq):
        if len(bset) < len(newSeq):
            if isSubset(bset, newSeq) and value*1.0/prefixDic[item] > 0.8:
                deleteList.append(item)
                #print "discard %s because %s"%(item, name)
        else:
            if isSubset(newSeq, bset) and prefixDic[item]*1.0/value > 0.8:
                 add = False
                 #print 'discard %s bec %s ' %(name,item)
   for item in deleteList:
        if item in prefixDic:
           del prefixDic[item]
            
   if add:
       #print 'add ',name
       prefixDic[name] = value
 
# project a sub-tree for a element
# root: tree root node
# item: element
# item2Ref: element->[nodes]
# threshold: support threshold for frequent pattern
# prefix: current frequent pattern
# prefixDic: already found frequent pattern dictionary
def project(root, item, item2Ref, threshold, prefix, prefixDic):
   nodelist = item2Ref[item]
   value = 0
   for node in nodelist:
      value += node.value
   if value < threshold:
      return 
   else:
      newRoot, newItem2ref=copyAndUpdateTree(root, item, item2Ref, prefix)
      #print 'item:', prefix+item
      #print 'newItem2ref',newItem2ref
      #print 'newTree:'
      #printTree(newRoot)
      """ 
      if prefix in prefixDic and value == prefixDic[prefix]:
         del prefixDic[prefix]
      prefix = prefix+' ' +item
      prefixDic[prefix]=value
      """
      prefix = prefix+' '+item
      discardItem(prefixDic, prefix, value) 
      for newitem in newItem2ref.keys():
         #print newitem
         project(newRoot, newitem, newItem2ref, threshold,prefix, prefixDic )

def getOrderedItemsAndDictionary(alist):
  item2q = {}
  for seq in alist:
    for item in seq.strip().split(' '):
      if item in item2q:
         item2q[item] += 1
      else:
         item2q[item] = 1
  sorted_x = sorted(item2q.iteritems(), key = operator.itemgetter(1), reverse = True)
  item2priority = {}
  p = len(sorted_x)
  ordered = []
  for k, v in sorted_x:
    item2priority[k] = p
    p -= 1
    ordered.append(k)
  return ordered, item2priority

def deleteSubSeq(k2v):
   items=k2v.keys()
   setList=[]
   deleteList=[]
   
   for item in items:
     for item2 in items:
         if len(item)<=len(item2):
            continue
         aset=item.strip().split(' ')
         bset=item2.strip().split(' ')
         if len(aset)>len(bset) and isSubset(bset, aset) and (k2v[item]*1.0/k2v[item2]) < SUPERSET_DISCARD_RATE:
             deleteList.append(item)
             #print "delete (%s,%d) because (%s,%d)"%(item,k2v[item],item2,k2v[item2])
             break;
   for item in deleteList:
     if item in k2v:
       del k2v[item]
   
def getFrequentPattern(sentenceList, support):
  orderedItem, orderDictionary = getOrderedItemsAndDictionary(sentenceList)
  root = TreeNode('',0)
  item2ref={}
  
  createTree(sentenceList,root, orderDictionary, item2ref)
  
  prefixDic={}
  for item in item2ref.keys():
     project(root, item, item2ref, support, "", prefixDic)
  
  if len(prefixDic)> 50:
     deleteSubSeq(prefixDic)
 
  sentenceExample = {}

  for k in prefixDic.keys():
     sentenceExample[k]=[]
     words=k.strip().split(' ')
     passed =True
     for sentence in sentenceList:
         passed = True
         if len(sentenceExample[k])>=5:
            break;
         for word in words:
            if sentence.find(word)<0:
               passed =False
         if passed:
            sentenceExample[k].append(sentence)

  return prefixDic,sentenceExample

if __name__ == '__main__':
  alist=['apple banana dog egg','banana cat egg','apple banana dog egg','apple banana cat egg','apple banana cat dog egg','banana cat dog']
  result = getFrequentPattern(alist, 2)
  print result

