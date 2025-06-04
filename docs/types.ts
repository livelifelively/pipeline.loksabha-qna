/**
 * Enhanced Module Graph Node Types
 *
 * Minimal node type definitions for graph-based representation.
 */

// Node ID types for type-safe references
export type ApplicationId = 'APP001';
export type InterfaceId = 'INT001';
export type ActorId = 'ACT001' | 'ACT002' | 'ACT003';
export type ModuleId = 'MOD001' | 'MOD002';
export type ClassId = 'CLS001' | 'CLS002';
export type FunctionId = 'FUN001' | 'FUN002' | 'FUN003' | 'FUN004';
export type UseCaseId = 'UC001';
export type CommandId = 'CMD001';

// Base node interface
export interface BaseNode {
  id: string;
  name: string;
  description: string;
}

// Actor node - system participants
export interface ActorNode extends BaseNode {
  category: 'human' | 'system' | 'ai';
  uses_interfaces?: InterfaceId[];
}

// Interface node - how users interact with the system
export interface InterfaceNode extends BaseNode {
  interface_type: 'cli' | 'web' | 'api';
  entry_module?: ModuleId;
  entry_class?: ClassId;
  entry_function?: FunctionId;
  execution?: {
    command?: CommandId;
    working_directory?: string;
    description?: string;
  };
  application?: ApplicationId;
  commands?: CommandId[];
  used_by?: ActorId[];
}

// Module node - files/modules
export interface ModuleNode extends BaseNode {
  path: string;
  application?: ApplicationId;
  entry_for_interfaces?: InterfaceId[];
  imports?: ModuleId[];
  imported_by?: ModuleId[];
  functions?: FunctionId[];
  classes?: ClassId[];
}

// Class node - classes within modules
export interface ClassNode extends BaseNode {
  module_id: ModuleId;
  inherits_from?: ClassId;
  functions?: FunctionId[];
}

// Function node - functions within modules
export interface FunctionNode extends BaseNode {
  module_id: ModuleId;
  class_id?: ClassId;
  instantiates?: ClassId[];
}

// Use case node - business functionality
export interface UseCaseNode extends BaseNode {
  primary_actor: ActorId;
  entry_function: FunctionId;
  entry_class: ClassId;
  entry_module: ModuleId;
}

// Command node - executable commands
export interface CommandNode extends BaseNode {
  command: string;
  working_directory: string;
  executable_by?: ActorId[];
}

// Application node - system context
export interface ApplicationNode extends BaseNode {
  domain: string;
  interfaces: InterfaceId[];
  modules?: ModuleId[];
}

// Edge types
export interface BaseEdge {
  from: string;
  to: string;
  type: string;
}

// Union types
export type GraphEdge = BaseEdge;
export type GraphNode =
  | ActorNode
  | InterfaceNode
  | ModuleNode
  | ClassNode
  | FunctionNode
  | UseCaseNode
  | ApplicationNode
  | CommandNode;

// Complete graph container
export interface EnhancedModuleGraph {
  metadata: {
    system_name: string;
    description: string;
    version: string;
  };

  nodes: {
    actors: Record<ActorId, ActorNode>;
    interfaces: Record<InterfaceId, InterfaceNode>;
    modules: Record<ModuleId, ModuleNode>;
    classes: Record<ClassId, ClassNode>;
    functions: Record<FunctionId, FunctionNode>;
    use_cases: Record<UseCaseId, UseCaseNode>;
    applications: Record<ApplicationId, ApplicationNode>;
    commands: Record<CommandId, CommandNode>;
  };
}
